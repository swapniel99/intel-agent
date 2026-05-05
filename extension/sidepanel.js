import { GoogleGenAI } from "./genai.js";

const MCP_URL = "http://localhost:8000/mcp";
const MODEL = "gemini-3.1-flash-lite-preview";
const API_KEY_STORAGE = "gemini_api_key";
const THEME_STORAGE = "theme";

const $dot = document.getElementById("server-dot");
const $status = document.getElementById("status-bar");
const $log = document.getElementById("log-section");
const $runBtn = document.getElementById("run-btn");
const $promptInput = document.getElementById("prompt-input");
const $dashboardFrame = document.getElementById("prefab-frame");
const $emptyState = document.getElementById("empty-state");
const DASHBOARD_URL = "http://localhost:8000/dashboard";
const $settingsBtn = document.getElementById("settings-btn");
const $themeBtn = document.getElementById("theme-btn");
const $settingsPanel = document.getElementById("settings-panel");
const $apiKeyInput = document.getElementById("api-key-input");
const $saveKeyBtn = document.getElementById("save-key-btn");
const $keyStatus = document.getElementById("key-status");
const $geminiSection = document.getElementById("gemini-section");
const $geminiContent = document.getElementById("gemini-content");

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
    clientInfo: { name: "AgentCurator", version: "1.0" },
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
  clearLog();
  clearGemini();
  $dashboardFrame.style.display = "none";
  $dashboardFrame.src = "about:blank";
  $emptyState.style.display = "none";

  const functionDeclarations = mcpToolsToFunctionDeclarations(mcpTools);

  const contents = [
    { role: "user", parts: [{ text: userPrompt }] },
  ];

  const now = new Date().toLocaleString();
  const systemInstruction = `You are AgentCurator, an AI research assistant. 
Current Date and Time: ${now}

Pick tools based on the user's intent.

Intent classification:
- ARTICLE_CURATION: user wants a list/feed/digest of articles.
  - Use fetch_tech_news for tech trends/community discussion.
  - Use Built-in Google Search for general news/product updates.
  → manage_local_library(check_duplicates) → manage_local_library(save_new) → render_prefab_dashboard
- TREND_ANALYSIS: user asks about trends/comparisons/visualization.
  - Gather data via fetch_tech_news or Google Search.
  → render_prefab_dashboard with chart={type, title, labels, values}
- COMBINED: articles + chart in one render_prefab_dashboard call (pass cards AND chart).

Rules:
- MERGE results from both internet tools when used together before calling library/dashboard.
- Use current date to filter stale results unless user asks historical.
- render_prefab_dashboard is the ONLY render tool. Pass cards (articles) and/or chart (visualization).
- chart.type ∈ bar, line, pie, area, scatter, radar, sparkline. Pick best fit.
- For render_prefab_dashboard: pass user's search subject verbatim as topic, pick best theme_key.
- NEVER emit chart specs, JSON, dashboard HTML, or data arrays inline. Use the tool.
- Text responses: 2-3 sentences max prose only. No code blocks, no structured data.
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
    const responseText = response.text;
    if (responseText) appendGemini(responseText);

    if (!toolCalls || toolCalls.length === 0) {
      setStatus("Done.", "success");
      return;
    }

    const toolResponseParts = [];

    for (const call of toolCalls) {
      const { name, args } = call;
      appendLog(`→ tool: ${name}`, "tool");

      let toolResult;
      try {
        toolResult = await callMcpTool(name, args);
      } catch (err) {
        toolResult = { error: err.message };
        appendLog(`  error: ${err.message}`, "warn");
      }

      appendLog(`  ← ${JSON.stringify(toolResult).slice(0, 120)}`, "result");

      if (name === "render_prefab_dashboard" && toolResult?.status === "dashboard_ready") {
        renderDashboard();
      }

      toolResponseParts.push({
        functionResponse: {
          name,
          response: { content: toolResult },
        },
      });
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

function appendLog(msg, type = "") {
  const el = document.createElement("div");
  el.className = `log-entry ${type}`;
  el.textContent = msg;
  $log.appendChild(el);
  $log.scrollTop = $log.scrollHeight;
}

function clearLog() {
  $log.innerHTML = "";
}

function renderMarkdown(src) {
  const esc = src
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return esc
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");
}

function appendGemini(text) {
  const el = document.createElement("div");
  el.className = "gemini-entry";
  el.innerHTML = `<p>${renderMarkdown(text.trim())}</p>`;
  $geminiContent.appendChild(el);
  $geminiSection.classList.add("visible");
  $geminiSection.scrollTop = $geminiSection.scrollHeight;
}

function clearGemini() {
  $geminiContent.innerHTML = "";
  $geminiSection.classList.remove("visible");
}

function renderDashboard() {
  $emptyState.style.display = "none";
  $dashboardFrame.style.display = "block";
  // Cache-bust so iframe re-fetches latest /dashboard HTML
  $dashboardFrame.src = `${DASHBOARD_URL}?t=${Date.now()}`;
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
    appendLog(`Loaded ${mcpTools.length} tools: ${mcpTools.map(t => t.name).join(", ")}`);
  } catch (_) {
    setServerStatus(false);
  }
}

function initGemini(apiKey) {
  ai = new GoogleGenAI({ apiKey });
}

function loadApiKey() {
  chrome.storage.local.get([API_KEY_STORAGE], result => {
    geminiApiKey = result[API_KEY_STORAGE] || "";
    if (geminiApiKey) {
      initGemini(geminiApiKey);
      $apiKeyInput.value = "••••••••••••••••";
    } else {
      setStatus("No API key — click ⚙️ to add one.");
    }
    $runBtn.disabled = !geminiApiKey;
  });
}

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
});

loadTheme();

$saveKeyBtn.addEventListener("click", () => {
  const key = $apiKeyInput.value.trim();
  if (!key || key.startsWith("•")) return;
  geminiApiKey = key;
  initGemini(key);
  chrome.storage.local.set({ [API_KEY_STORAGE]: key }, () => {
    $apiKeyInput.value = "••••••••••••••••";
    $keyStatus.textContent = "Saved.";
    $runBtn.disabled = false;
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
    appendLog(`Error: ${err.message}`, "warn");
  } finally {
    $runBtn.disabled = false;
  }
});

$promptInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) $runBtn.click();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes[API_KEY_STORAGE]?.newValue) {
    geminiApiKey = changes[API_KEY_STORAGE].newValue;
    initGemini(geminiApiKey);
    $runBtn.disabled = false;
    setStatus("API key updated. Enter a prompt.");
  }
});

loadApiKey();
checkServer();
