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
const $dashboardRoot = document.getElementById("prefab-root");
const $chartRoot = document.getElementById("chart-root");
const $emptyState = document.getElementById("empty-state");
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
  $chartRoot.style.display = "none";
  $chartRoot.innerHTML = "";
  $dashboardRoot.style.display = "none";
  $dashboardRoot.innerHTML = "";
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
- TREND_ANALYSIS: user asks about trends, comparisons, or data visualization.
  - Use fetch_tech_news for community trends.
  - Use Built-in Google Search for factual/market trends.
  → render_analytics_chart
- COMBINED: run full research pipeline + chart + dashboard.

Rules:
- MERGE results from both internet tools when used together before calling the library/dashboard tools.
- Use the current date to filter out stale or irrelevant results unless the user specifically asks for historical data.
- Only call render_prefab_dashboard if user wants articles displayed.
- Only call render_analytics_chart if user wants a chart, graph, or trend visualization.
- For render_prefab_dashboard: pass user's search subject verbatim as topic, pick best theme_key.
- NEVER emit chart specs, JSON, or data arrays inline in your text response. If chart is needed, you MUST invoke render_analytics_chart tool with the data. Inline JSON output is forbidden.
- NEVER emit dashboard HTML/markdown inline. Use render_prefab_dashboard tool.
- Text responses are for short prose summaries only — no code blocks, no structured data.
- Keep text responses to 2-3 sentences max. Brief commentary only. Data lives in the tool-rendered chart/dashboard, not your text.
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
        renderDashboard(toolResult);
      }

      if (name === "render_analytics_chart" && toolResult?.status === "chart_ready") {
        renderChart(toolResult);
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

function renderDashboard({ topic, theme, cards }) {
  $emptyState.style.display = "none";
  $dashboardRoot.style.display = "block";
  const { emoji, hue, bg, card: cardBg, fg, muted, border } = theme;
  const accent = `oklch(0.72 0.20 ${hue})`;

  const cardHtml = cards.length === 0
    ? `<p style="color:${muted}">No articles to display.</p>`
    : cards.map(c => `
        <div style="background:${cardBg};border:1px solid ${border};border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:6px">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px">
            <span style="font-weight:600;font-size:13px;line-height:1.4;color:${fg}">${escHtml(c.title)}</span>
            <span style="flex-shrink:0;font-size:11px;padding:2px 7px;border-radius:999px;background:${accent}22;color:${accent};border:1px solid ${accent}55">▲ ${c.points}</span>
          </div>
          <a href="${escHtml(c.url)}" target="_blank" style="font-size:12px;color:${accent};word-break:break-all;text-decoration:underline">${escHtml(c.url)}</a>
          ${c.ai_summary ? `<p style="font-size:12px;color:${muted};margin-top:2px">${escHtml(c.ai_summary)}</p>` : ""}
        </div>`).join("");

  $dashboardRoot.innerHTML = `
    <div style="background:${bg};min-height:100%;padding:16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
      <h2 style="font-size:16px;font-weight:700;color:${fg};margin-bottom:14px">${emoji} ${escHtml(topic)}</h2>
      <div style="display:flex;flex-direction:column;gap:10px">${cardHtml}</div>
    </div>`;
}

function renderChart({ title, type, data }) {
  $emptyState.style.display = "none";
  $chartRoot.style.display = "block";
  $chartRoot.innerHTML = ""; // Clear old chart
  new frappe.Chart("#chart-root", {
    title,
    data,
    type,
    height: 180,
    colors: ["#2563eb"],
    axisOptions: { xAxisMode: "tick", xIsSeries: true },
  });
}

function escHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
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
