# Product Requirements Document (PRD)
## Project Name: AgentCurator (AI Trend Curation Engine)

**Objective:** Build a decoupled AI system where a Chrome Extension Side Panel (Orchestrator/UI) connects via Server-Sent Events (SSE) to a local Python FastAPI backend (MCP Server) to fetch internet data, perform local file CRUD, and dynamically render a Prefab UI.

**Target Output:** A 2500-point assignment submission including a GitHub repo, a YouTube demo showing agent logs, and a LinkedIn showcase.

---

### 1. Executive Summary
AgentCurator is a personal AI research assistant designed to combat information overload. It operates entirely within the user's browser via a Chrome Extension Side Panel, providing a persistent companion UI. It securely orchestrates tasks by delegating them to a local Python MCP server. The agent fetches trending articles, deduplicates them against a local JSON ledger, writes personalized summaries, and renders a dynamic, visually appealing reading dashboard using Prefab.

### 2. System Architecture
This project utilizes a highly decoupled, production-ready pattern.

*   **The Orchestrator & Frontend (Chrome Extension Side Panel):** Handles the user interface, maintains the connection to the Gemini API, and parses the final UI payload. We will use `pnpm` for frontend package management.
*   **The MCP Server (Python 3.14 + FastMCP):** Runs locally on `http://localhost:8000` (or default FastMCP port). It executes the actual tool logic (internet fetch, local file CRUD) and streams responses back to the extension via FastMCP's built-in SSE transport.
*   **LLM Provider:** Google Gemini API.

---

### 3. Frontend Implementation: Chrome Extension (Manifest V3)

The frontend will act as the "Brain" (Orchestrator) and the "Face" (UI).

#### A. Extension Structure & Permissions
We will use a persistent Side Panel approach to ensure the agent is not interrupted if the user clicks away from the extension.

*   **Manifest Configuration:**
    ```json
    {
      "manifest_version": 3,
      "name": "AgentCurator: MCP Assistant",
      "version": "1.0",
      "permissions": ["sidePanel", "storage"],
      "host_permissions": [
        "http://localhost:8000/*",
        "https://*.googleapis.com/*"
      ],
      "background": {
        "service_worker": "background.js"
      },
      "side_panel": {
        "default_path": "sidepanel.html"
      },
      "action": {
        "default_title": "Open AgentCurator"
      }
    }
    ```
    *(Note: `background.js` will contain a single listener to open the side panel when the extension icon is clicked: `chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });`)*

#### B. The Orchestrator Logic (`sidepanel.js`)
*   **Gemini Execution:** All calls to the Gemini API will happen directly within `sidepanel.js`.
*   **Dynamic Tool Binding (Point D):** On initialization, `sidepanel.js` will POST to `http://localhost:8000/mcp` using the MCP `tools/list` method to discover available tools. It will parse the returned tool definitions and inject them into the `tools: [{ functionDeclarations: [...] }]` payload for Gemini. *(Note: FastMCP 3.x serves all MCP protocol at `/mcp` — there is no separate `/tools` REST endpoint.)*
*   **Tool Execution Loop:** When Gemini requests a tool call, `sidepanel.js` intercepts it, sends a `tools/call` POST to `http://localhost:8000/mcp`, and feeds the result back to Gemini.

#### C. Prefab Rendering Strategy (Point C)
*   The final tool (`render_prefab_dashboard`) returns a **complete self-contained HTML page** built with `prefab-ui` components (`Card`, `Badge`, `Link`, etc.), with the Prefab renderer loaded from jsDelivr CDN.
*   `sidepanel.js` captures this HTML string and renders it by setting it as the `srcdoc` attribute of an `<iframe>` in the side panel: `document.getElementById('prefab-frame').srcdoc = prefabHTML;`.
*   **Why `<iframe srcdoc>` not `innerHTML`:** The Prefab HTML contains `<script type="module">` tags that browsers will not execute when injected via `innerHTML` (security restriction). An iframe gives the content its own document context where scripts run normally.
*   No additional Prefab CSS/JS needs to be linked in `sidepanel.html` — the renderer is self-contained inside the returned HTML.

---

### 4. Backend Implementation: Python MCP Server

The backend will act as the "Hands," securely interacting with the OS and the internet.

*   **Framework:** Python 3.14 + FastMCP.
*   **Connection Protocol:** Server-Sent Events (SSE) for one-way streaming and standard HTTP POSTs for tool invocation, handled automatically by FastMCP's SSE transport.

#### The 3 Core Tools (Required for Assignment)

**Tool 1: `fetch_tech_news` (Internet Data)**
*   **Description:** Reaches out to the internet to find trending articles.
*   **Implementation:** GET request to `[http://hn.algolia.com/api/v1/search?query=](http://hn.algolia.com/api/v1/search?query=){query}&hitsPerPage={limit}`.
*   **Returns:** Cleaned array of article objects `[{title, url, points}]`.

**Tool 2: `manage_local_library` (Local File CRUD)**
*   **Description:** Handles Read, Append, and Delete operations on a local `saved_articles.json` file.
*   **Logic:**
    *   *Action = "check_duplicates":* Reads local file, compares URLs, returns only novel articles.
    *   *Action = "save_new":* Appends new articles to the JSON file.
*   **Returns:** Status string for the Agent (e.g., `"2 duplicates skipped. 3 new articles saved."`).

**Tool 3: `render_prefab_dashboard` (UI Communication)**
*   **Description:** Compiles the final curated data into a Prefab UI dashboard using `prefab-ui` Python components.
*   **Parameters:** `cards` (array of curated articles with Gemini's summaries).
*   **Returns:** A complete self-contained HTML page (Prefab renderer loaded from CDN) that the Chrome Extension renders in an `<iframe srcdoc>`.

#### D. Backend Security & CORS
*   The FastMCP server MUST implement **CORS (Cross-Origin Resource Sharing) middleware** (accessible via its underlying Starlette/FastAPI app configuration). Because the Chrome Extension makes requests from a `chrome-extension://<id>` origin, the local server will reject them by default. Configure the middleware to allow origins from Chrome extensions (e.g., `allow_origins=["*"]` or specifically `chrome-extension://*`) and allow all necessary methods/headers.

---

### 5. Data Schemas & Error Handling

#### A. Data Schemas
To ensure reliable communication between the internet, the local file, and the UI, we must enforce strict schemas:

*   **`saved_articles.json` Schema:**
    An array of objects containing at minimum:
    `{ "id": "string", "title": "string", "url": "string", "points": "integer", "ai_summary": "string", "saved_at": "iso-timestamp" }`

*   **Prefab UI Output:**
    `render_prefab_dashboard` returns a complete HTML page produced by `PrefabApp.html()` using `prefab-ui` components (`Card`, `CardHeader`, `CardTitle`, `CardContent`, `Badge`, `Link`, `Span`, `Column`, `Heading`). The Prefab renderer JS/CSS is loaded from jsDelivr CDN, pinned to the installed `prefab-ui` version.

#### B. Error Handling & Edge Cases
*   **API Failures (Internet Fallback):** If `fetch_tech_news` fails due to an Algolia API timeout, rate limit, or network error, the system must gracefully fall back. The backend should catch the exception, pull the most recently saved articles from `saved_articles.json`, and return a status message to the agent/user stating: *"The internet source is currently unavailable. Displaying previously saved articles from your local storage."*
*   **Backend Disconnection:** If the Chrome Extension cannot reach `localhost:8000` (e.g., the python server isn't running), the side panel should display a clear "Server Disconnected" UI state rather than failing silently.

---

### 6. Data Flow & Demo Sequence

To guarantee maximum points on the YouTube submission, the execution flow must clearly demonstrate the agent chaining tools.

1.  **User Prompt (in Side Panel):** *"Agent, fetch the top 4 articles on 'Local LLMs'. Filter out duplicates against my local file, save the new ones, and generate a Prefab dashboard."*
2.  **Orchestrator:** Passes prompt + dynamically loaded tools to Gemini.
3.  **Tool Chain Execution:**
    *   Gemini requests `fetch_tech_news`. Python server executes and returns data.
    *   Gemini requests `manage_local_library("check_duplicates")`. Python server executes and returns filtered data.
    *   Gemini requests `manage_local_library("save_new")`. Python server writes to the local OS.
    *   Gemini requests `render_prefab_dashboard`. Python server returns the UI schema.
4.  **Final Render:** Side Panel sets the returned HTML as `<iframe srcdoc>` and the Prefab UI instantly appears on screen.

---

### 7. Testing Strategy

Before recording the final demo, developers should ensure stability via:
1.  **Backend Unit Tests (Python):** Use `pytest` to test the file CRUD operations (`manage_local_library`) in isolation, ensuring it correctly deduplicates URLs without modifying existing valid data. Mock the Algolia API to test the fallback mechanism if the internet is down.
2.  **Integration Testing (Postman/Curl):** Manually test the `/mcp` endpoint using MCP `tools/list` and `tools/call` JSON-RPC requests to ensure CORS is correctly configured and tool responses are returned correctly.
3.  **UI/UX Verification:** Force an API failure to verify the "source not available" fallback message and local storage data render correctly in the Prefab UI.

---

### 8. Acceptance Criteria for Submission

*   [x] Architecture utilizes decoupled frontend (Chrome Extension) and backend (Python).
*   [x] Communication uses SSE and REST endpoints.
*   [x] MCP server implements exactly 3 distinct functions.
*   [x] System performs an Internet fetch (Function 1).
*   [x] System performs Local File CRUD (Function 2).
*   [x] System communicates back to a UI using Prefab (Function 3).
*   [x] Gemini API dynamically registers tools via MCP `tools/list` at `/mcp`.
*   [x] Prompt forces the agent to chain all three functions sequentially.
