import { GoogleGenAI } from "./genai.js";

let MCP_URL = "http://localhost:8000/mcp";
const MODEL = "gemini-3.1-flash-lite-preview";
const API_KEY_STORAGE = "gemini_api_key";
const MCP_SERVER_URL_STORAGE = "mcp_server_url";
const THEME_STORAGE = "theme";

const $dot = document.getElementById("server-dot");
const $status = document.getElementById("status-bar");
const $runBtn = document.getElementById("run-btn");
const $promptInput = document.getElementById("prompt-input");
const $dashboardFrame = document.getElementById("prefab-frame");
const $emptyState = document.getElementById("empty-state");
let DASHBOARD_URL = "http://localhost:8000/dashboard";
const $settingsBtn = document.getElementById("settings-btn");
const $themeBtn = document.getElementById("theme-btn");
const $settingsPanel = document.getElementById("settings-panel");
const $apiKeyInput = document.getElementById("api-key-input");
const $mcpUrlInput = document.getElementById("mcp-url-input");
const $saveSettingsBtn = document.getElementById("save-settings-btn");
const $keyStatus = document.getElementById("key-status");
const $resetBtn = document.getElementById("reset-btn");

let mcpTools = [];
let geminiApiKey = "";
let mcpSessionId = null;
let ai = null;

// ── MCP helpers ──────────────────────────────────────────────────────────────

async function mcpRequest(method, params = {}) {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
  };
  if (mcpSessionId) headers["mcp-session-id"] = mcpSessionId;

  let res = await fetch(MCP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }),
  });

  // Handle server restart / session loss (404 Not Found)
  if (res.status === 404 && mcpSessionId) {
    console.warn("MCP session not found (server likely restarted). Re-initializing...");
    mcpSessionId = null;
    await mcpInitialize(); // Re-initialize connection

    // Retry the original request with new session
    const newHeaders = { ...headers };
    if (mcpSessionId) newHeaders["mcp-session-id"] = mcpSessionId;
    res = await fetch(MCP_URL, {
      method: "POST",
      headers: newHeaders,
      body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }),
    });
  }

  if (res.headers.get("mcp-session-id")) {
    mcpSessionId = res.headers.get("mcp-session-id");
  }

  const contentType = res.headers.get("content-type") || "";

  if (contentType.includes("text/event-stream")) {
    return parseSseResponse(res);
  }

  const json = await res.json();
  if (json.error) throw new Error(json.error.message || JSON.stringify(json.error));
  return json.result;
}

async function parseSseResponse(res) {
  const text = await res.text();
  for (const line of text.split("\n")) {
    if (line.startsWith("data: ")) {
      try {
        const json = JSON.parse(line.slice(6));
        if (json.result !== undefined) return json.result;
        if (json.error) throw new Error(json.error.message || JSON.stringify(json.error));
      } catch (_) { /* skip non-JSON data lines */ }
    }
  }
  throw new Error("No result in SSE stream");
}

async function mcpInitialize() {
  await mcpRequest("initialize", {
    protocolVersion: "2024-11-05",
    clientInfo: { name: "IntelAgent", version: "1.0" },
    capabilities: {},
  });
}

async function loadMcpTools() {
  const result = await mcpRequest("tools/list");
  return result.tools || [];
}

async function callMcpTool(name, args) {
  const result = await mcpRequest("tools/call", { name, arguments: args });
  if (result.isError) throw new Error(result.content?.[0]?.text || "Tool error");
  const content = result.content?.[0];
  if (!content) return null;
  if (content.type === "text") {
    try { return JSON.parse(content.text); } catch (_) { return content.text; }
  }
  return content;
}

// ── Gemini helpers ────────────────────────────────────────────────────────────

function mcpToolsToFunctionDeclarations(tools) {
  return tools.map(t => ({
    name: t.name,
    description: t.description || "",
    parameters: t.inputSchema || { type: "object", properties: {} },
  }));
}

// ── Agent loop ────────────────────────────────────────────────────────────────

async function runAgent(userPrompt) {
  setStatus("Running agent…");
  $dashboardFrame.style.display = "none";
  $dashboardFrame.src = "about:blank";
  $emptyState.style.display = "none";

  const functionDeclarations = mcpToolsToFunctionDeclarations(mcpTools);

  const contents = [
    { role: "user", parts: [{ text: userPrompt }] },
  ];

  const now = new Date().toLocaleString();
  const systemInstruction = `You are IntelAgent, an AI research assistant.
Current Date and Time: ${now}

Pick tools based on the user's intent.

Intent classification:
- HYBRID_RESEARCH: latest info + saved knowledge.
  → manage_local_library(search) → fetch_tech_news(source='all') OR Google Search → dedupe & summarize → MERGE all results → manage_local_library(save_new) → render_prefab_dashboard
- ARTICLE_CURATION: list/feed/digest of new articles.
  → fetch_tech_news(source='all') → dedupe & summarize → manage_local_library(save_new) → render_prefab_dashboard
- LIBRARY_MANAGEMENT: browse, search, or clean local collection.
  → render_prefab_dashboard
- TREND_ANALYSIS: comparisons and data visualization.
  - Gather data → PROACTIVELY identify quantitative metrics (counts, shares, trends) → include a chart → render_prefab_dashboard

Rules (CRITICAL):
- ALWAYS call 'render_prefab_dashboard' when you are finished and ready to show the results to the user. This is MANDATORY for providing your final answer.
- Put your complete response to the user in the 'ai_answer' parameter of render_prefab_dashboard. Do NOT emit text outside of tool calls — the dashboard is the only output surface.
- Include a chart ONLY when the user explicitly asks for analysis/comparison/trends OR when the fetched data has meaningful quantitative differences worth visualizing. Pure news/article fetches: NO chart.
- ai_answer: 2-3 sentences max, prose only, no code blocks.
`;

  const MAX_TURNS = 12;

  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const response = await ai.models.generateContent({
      model: MODEL,
      contents,
      config: {
        systemInstruction,
        tools: [
          { functionDeclarations: functionDeclarations.length ? functionDeclarations : [] },
          { googleSearch: {} }
        ],
        toolConfig: {
          functionCallingConfig: {
            mode: "AUTO",
          },
          googleSearchRetrieval: {
            dynamicRetrievalConfig: {
              mode: "DYNAMIC",
              dynamicThreshold: 0.3,
            }
          },
          includeServerSideToolInvocations: true,
        },
        generationConfig: { temperature: 0.2 },
      },
    });

    const candidate = response.candidates?.[0];
    if (!candidate) throw new Error("No candidates in Gemini response");

    const parts = candidate.content?.parts || [];
    contents.push({ role: "model", parts });

    const toolCalls = response.functionCalls;

    if (!toolCalls || toolCalls.length === 0) {
      const textResponse = parts.map(p => p.text || "").join("\n").trim();
      if (textResponse) {
        setStatus("Rendering fallback…");
        try {
          await callMcpTool("render_prefab_dashboard", {
            cards: [],
            topic: "Research Result",
            ai_answer: textResponse
          });
          renderDashboard();
          setStatus("Done.", "success");
        } catch (err) {
          setStatus(`Fallback Error: ${err.message}`, "error");
        }
      } else {
        setStatus("Done.", "success");
      }
      return;
    }

    const toolResponseParts = [];

    let dashboardRendered = false;
    for (const call of toolCalls) {
      const { name, args } = call;

      let toolResult;
      try {
        toolResult = await callMcpTool(name, args);
      } catch (err) {
        toolResult = { error: err.message };
      }

      if (name === "render_prefab_dashboard" && toolResult?.status === "dashboard_ready") {
        renderDashboard();
        dashboardRendered = true;
      }

      toolResponseParts.push({
        functionResponse: {
          name,
          response: { content: toolResult },
        },
      });
    }

    if (dashboardRendered) {
      setStatus("Done.", "success");
      return;
    }

    contents.push({ role: "user", parts: toolResponseParts });
  }

  setStatus("Max turns reached.", "error");
}

// ── UI helpers ────────────────────────────────────────────────────────────────

function setStatus(msg, type = "") {
  $status.textContent = msg;
  $status.className = type;
}

function renderDashboard() {
  $emptyState.style.display = "none";
  $dashboardFrame.style.display = "block";
  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  // Cache-bust so iframe re-fetches latest /dashboard HTML
  $dashboardFrame.src = `${DASHBOARD_URL}?theme=${theme}&t=${Date.now()}`;
}

function setServerStatus(online) {
  $dot.className = online ? "dot" : "dot offline";
  setStatus(
    online
      ? "Server connected. Enter a prompt."
      : "Server offline — run: python main.py"
  );
  $runBtn.disabled = !online || !geminiApiKey;
}

// ── Init ──────────────────────────────────────────────────────────────────────

async function checkServer() {
  try {
    await mcpInitialize();
    mcpTools = await loadMcpTools();
    setServerStatus(true);
  } catch (_) {
    setServerStatus(false);
  }
}

function initGemini(apiKey) {
  ai = new GoogleGenAI({ apiKey });
}

function loadSettings() {
  chrome.storage.local.get([API_KEY_STORAGE, MCP_SERVER_URL_STORAGE], result => {
    geminiApiKey = result[API_KEY_STORAGE] || "";
    if (geminiApiKey) {
      initGemini(geminiApiKey);
      $apiKeyInput.value = "••••••••••••••••";
    } else {
      setStatus("No API key — click ⚙️ to add one.");
    }

    const serverUrl = result[MCP_SERVER_URL_STORAGE] || "http://localhost:8000";
    $mcpUrlInput.value = serverUrl;
    MCP_URL = `${serverUrl.replace(/\/$/, "")}/mcp`;
    DASHBOARD_URL = `${serverUrl.replace(/\/$/, "")}/dashboard`;

    $runBtn.disabled = !geminiApiKey;
    checkServer();
  });
}

async function resetConnection() {
  mcpSessionId = null;
  setStatus("Resetting connection…");
  $dashboardFrame.style.display = "none";
  $emptyState.style.display = "flex";
  $runBtn.disabled = true;
  await checkServer();
}

$resetBtn.addEventListener("click", resetConnection);

$settingsBtn.addEventListener("click", () => {
  const visible = $settingsPanel.classList.toggle("visible");
  $settingsBtn.classList.toggle("active", visible);
});

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  $themeBtn.textContent = theme === "dark" ? "🌙" : "☀️";
}

function loadTheme() {
  chrome.storage.local.get([THEME_STORAGE], result => {
    applyTheme(result[THEME_STORAGE] || "dark");
  });
}

$themeBtn.addEventListener("click", () => {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  applyTheme(next);
  chrome.storage.local.set({ [THEME_STORAGE]: next });
  if ($dashboardFrame.style.display !== "none") {
    renderDashboard();
  }
});

$saveSettingsBtn.addEventListener("click", () => {
  const key = $apiKeyInput.value.trim();
  const serverUrl = $mcpUrlInput.value.trim() || "http://localhost:8000";

  const settings = {
    [MCP_SERVER_URL_STORAGE]: serverUrl
  };

  if (key && !key.startsWith("•")) {
    geminiApiKey = key;
    initGemini(key);
    settings[API_KEY_STORAGE] = key;
    $apiKeyInput.value = "••••••••••••••••";
  }

  const cleanUrl = serverUrl.replace(/\/$/, "");
  MCP_URL = `${cleanUrl}/mcp`;
  DASHBOARD_URL = `${cleanUrl}/dashboard`;

  chrome.storage.local.set(settings, () => {
    $keyStatus.textContent = "Settings saved.";
    $runBtn.disabled = !geminiApiKey;
    setTimeout(() => { $keyStatus.textContent = ""; }, 2000);
    checkServer();
  });
});

$runBtn.addEventListener("click", async () => {
  const prompt = $promptInput.value.trim();
  if (!prompt || !geminiApiKey) return;

  $runBtn.disabled = true;
  try {
    await runAgent(prompt);
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    $runBtn.disabled = false;
  }
});

$promptInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $runBtn.click();
  }
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes[API_KEY_STORAGE]?.newValue) {
    geminiApiKey = changes[API_KEY_STORAGE].newValue;
    initGemini(geminiApiKey);
    $runBtn.disabled = false;
    setStatus("API key updated. Enter a prompt.");
  }
});

loadTheme();
loadSettings();
