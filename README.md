# 🔍 IntelAgent

> **AI-Powered Research Assistant** — A production-ready orchestration of a Chrome Extension Side Panel and a local Python MCP backend.

IntelAgent bridges the gap between high-level AI reasoning and local system capabilities. It empowers users to fetch trending news from multiple sources, ground facts with Google Search, manage findings against a local JSON ledger, and visualize data through a beautiful, interactive Prefab dashboard.

---

## ✨ Key Features

- **🌐 Multi-Source Research:** Seamlessly fetches from **Hacker News**, **Dev.to**, and **Reddit**, combined with broad factual grounding via **Google Search** (Dynamic Grounding).
- **📚 Local Memory:** Persistent JSON library (`saved_articles.json`) for article deduplication, full-text search, and historical research tracking.
- **📊 Dynamic Dashboards:** Automatically generates rich UI dashboards using **Prefab UI** and **Frappe Charts** (Bar, Pie, Line, Area, Radar, Radial).
- **🧩 MCP Native:** Built on the **Model Context Protocol (FastMCP)** for robust, standardized communication between the LLM and local tools.
- **⚡ Persistence:** Operates in a Chrome **Side Panel** (Manifest V3) for an uninterrupted, always-available research companion.

---

## 🏗️ Architecture

```mermaid
graph TD
    User([User Prompt]) --> Extension[Chrome Extension Side Panel]
    Extension --> Gemini
    Gemini -- Tool Discovery --> FastMCP[FastMCP Server :8000]
    FastMCP -- Tool Definition --> Gemini

    subgraph "Local Tools (Python)"
        FastMCP --> T1[fetch_tech_news]
        FastMCP --> T2[manage_local_library]
        FastMCP --> T3[render_prefab_dashboard]
        T1 --> HN[Hacker News / Dev.to / Reddit]
        T2 --> JSON[(saved_articles.json)]
        T3 --> Cache[_LAST_DASHBOARD_HTML]
    end

    Gemini -- Dynamic Grounding --> Google[Google Search]
    Gemini -- Tool Call --> FastMCP
    FastMCP -- status: dashboard_ready --> Extension
    Extension -- GET /dashboard?theme=... --> Cache
    Cache -- HTML Page --> Dashboard{{iframe Dashboard}}
```

---

## 🚀 Getting Started

### 1. Backend Setup (MCP Server)
The backend requires Python 3.14+ and `uv` (recommended).

```bash
# Clone the repo
git clone https://github.com/swapniel/intel-agent.git
cd intel-agent

# Install dependencies using uv
uv sync

# Start the server (uses the virtual environment automatically)
./.venv/bin/python main.py
```
*The server will run on `http://localhost:8000`. Keep this terminal open.*

### 2. Frontend Setup (Chrome Extension)
1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select the `extension` folder in this repository.
4. Click the IntelAgent icon in your toolbar to open the **Side Panel**.
5. Click the gear icon (⚙️) to enter your **Gemini API Key**.

---

## 🛠️ Integrated Tools

| Tool | Capability | Source/Target |
|---|---|---|
| `fetch_tech_news` | Retrieves trending tech discussions from multiple sources. | Hacker News, Dev.to, Reddit |
| `manage_local_library` | Full CRUD on research: `check_duplicates`, `save_new`, `list_all`, `search`, `update`, `delete`. | `saved_articles.json` |
| `render_prefab_dashboard` | Compiles research into a rich HTML dashboard. Supports 6 chart types and auto-theme matching. | Prefab UI + Frappe Charts |
| **Google Search** | (Native) Provides real-time factual grounding for general queries. | Google Search Index |

### Dashboard Chart Support
- **Comparison:** Bar, Line, Area
- **Composition:** Pie, Radial
- **Multivariate:** Radar

---

## 📖 Usage Example

**Prompt:**
> "Find the top 3 articles on 'Quantum Computing' from Hacker News. Compare them with recent breakthroughs found on Google Search. Save the new ones and show me a dashboard with a market interest chart."

**Execution Flow:**
1. **Search:** Gemini calls `fetch_tech_news` and performs a grounded Google Search.
2. **Filter:** Gemini calls `manage_local_library(check_duplicates)` to see what's already saved.
3. **Summarize:** Gemini generates concise, 1-sentence summaries for the new findings.
4. **Persist:** Gemini calls `manage_local_library(save_new)` to update your local ledger.
5. **Visualize:** Gemini calls `render_prefab_dashboard` with curated cards and a relevant chart.
6. **Result:** The Side Panel updates instantly with a professional research report.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.14, [FastMCP](https://github.com/jlowin/fastmcp), FastAPI, Uvicorn, Prefab-UI.
- **Frontend:** JavaScript (ES6+), Manifest V3, Gemini SDK.
- **Storage:** Local JSON filesystem.
- **AI:** Google Gemini with Dynamic Grounding.

---

## 📝 License

MIT © [Swapniel](https://github.com/swapniel)
