import { GoogleGenAI } from "./genai.js";
import { GeminiProvider } from "./providers/gemini-provider.js";
import { OllamaProvider } from "./providers/ollama-provider.js";

let MCP_URL = "http://localhost:8000/mcp";
const GEMINI_MODEL_STORAGE = "gemini_model";
const DEFAULT_GEMINI_MODEL = "gemini-3.5-flash";
const API_KEY_STORAGE = "gemini_api_key";
const MCP_SERVER_URL_STORAGE = "mcp_server_url";
const THEME_STORAGE = "theme";
const LLM_PROVIDER_STORAGE = "llm_provider";
const OLLAMA_URL_STORAGE = "ollama_url";
const OLLAMA_MODEL_STORAGE = "ollama_model";
const OLLAMA_THINKING_STORAGE = "ollama_thinking";
const DEFAULT_OLLAMA_URL = "http://localhost:11434";
const DEFAULT_OLLAMA_MODEL = "gemma4:26b";

const $dot = document.getElementById("server-dot");
const $status = document.getElementById("status-bar");
const $runBtn = document.getElementById("run-btn");
const $promptInput = document.getElementById("prompt-input");
const $dashboardFrame = document.getElementById("prefab-frame");
const $emptyState = document.getElementById("empty-state");
const $chatHistory = document.getElementById("chat-history");
let DASHBOARD_URL = "http://localhost:8000/dashboard";
const $settingsBtn = document.getElementById("settings-btn");
const $themeBtn = document.getElementById("theme-btn");
const $settingsPanel = document.getElementById("settings-panel");
const $apiKeyInput = document.getElementById("api-key-input");
const $mcpUrlInput = document.getElementById("mcp-url-input");
const $saveSettingsBtn = document.getElementById("save-settings-btn");
const $keyStatus = document.getElementById("key-status");
const $resetBtn = document.getElementById("reset-btn");
const $resizer = document.getElementById("resizer");
const $dashboardPanel = document.getElementById("dashboard-panel");
const $chatPanel = document.getElementById("chat-panel");
const $mainView = document.getElementById("main-view");
const $undoBtn = document.getElementById("undo-btn");
const $clearBtn = document.getElementById("clear-btn");
const $presetSentiment = document.getElementById("preset-sentiment");
const $presetRadar = document.getElementById("preset-radar");
const $presetPie = document.getElementById("preset-pie");
const $presetTrends = document.getElementById("preset-trends");
const $presetRankings = document.getElementById("preset-rankings");
const $presetAnalysis = document.getElementById("preset-analysis");
const $providerSelect = document.getElementById("provider-select");
const $ollamaSettings = document.getElementById("ollama-settings");
const $ollamaUrlInput = document.getElementById("ollama-url-input");
const $ollamaModelInput = document.getElementById("ollama-model-input");
const $geminiSettings = document.getElementById("gemini-settings");
const $geminiModelInput = document.getElementById("gemini-model-input");
const $ollamaThinkingToggle = document.getElementById("ollama-thinking-toggle");

let mcpTools = [];
let geminiApiKey = "";
let mcpSessionId = null;
let ai = null;
let activeProvider = null;
let currentProviderType = "gemini";
let conversationHistory = [];
let userPromptHistory = [];
let conversationCheckpoints = [];
let isResizing = false;

// ── MCP helpers ──────────────────────────────────────────────────────────────

async function mcpRequest(method, params = {}, retries = 2) {
  const headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
  };
  if (mcpSessionId) headers["mcp-session-id"] = mcpSessionId;

  let lastErr, res;
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      res = await Promise.race([
        fetch(MCP_URL, {
          method: "POST",
          headers,
          body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }),
        }),
        new Promise((_, reject) => setTimeout(() => reject(new Error("Request timeout")), 20000)),
      ]);
      break;
    } catch (err) {
      lastErr = err;
      if (attempt < retries - 1) {
        console.warn(`MCP request attempt ${attempt + 1} failed, retrying...`, err.message);
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }

  if (!res) throw lastErr;

  if (res.status === 404 && mcpSessionId) {
    console.warn("MCP session not found (server likely restarted). Re-initializing...");
    mcpSessionId = null;
    await mcpInitialize();

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

// ── Provider helpers ──────────────────────────────────────────────────────────

function mcpToolsToFunctionDeclarations(tools) {
  return tools.map(t => ({
    name: t.name,
    description: t.description || "",
    parameters: t.inputSchema || { type: "object", properties: {} },
  }));
}

function initProvider(type, { apiKey, geminiModel, ollamaUrl, ollamaModel, ollamaThinking } = {}) {
  currentProviderType = type;
  if (type === "ollama") {
    activeProvider = new OllamaProvider(
      ollamaUrl || DEFAULT_OLLAMA_URL,
      ollamaModel || DEFAULT_OLLAMA_MODEL,
      !!ollamaThinking
    );
  } else {
    if (apiKey) {
      ai = new GoogleGenAI({ apiKey });
      activeProvider = new GeminiProvider(ai, geminiModel || DEFAULT_GEMINI_MODEL);
    } else {
      activeProvider = null;
    }
  }
}

function isProviderReady() {
  if (currentProviderType === "ollama") return activeProvider !== null;
  return !!geminiApiKey && activeProvider !== null;
}

// ── Agent loop ────────────────────────────────────────────────────────────────

async function runAgent(userPrompt) {
  const checkpointLength = conversationHistory.length;
  userPromptHistory.push(userPrompt);
  conversationCheckpoints.push(checkpointLength);
  appendChatMessage(userPrompt, "user");
  updateChatButtonStates();
  $promptInput.value = "";

  setStatus("Running agent…");
  if (conversationHistory.length === 0) {
    $dashboardFrame.style.display = "none";
    $dashboardFrame.src = "about:blank";
    $emptyState.style.display = "none";
  }

  const functionDeclarations = mcpToolsToFunctionDeclarations(mcpTools);

  const userTurn = { role: "user", parts: [{ text: userPrompt }] };
  conversationHistory.push(userTurn);
  const contents = conversationHistory;
  console.log(`[Agent Init] history length: ${contents.length}`);

  const now = new Date().toLocaleString();
  const systemInstruction = `You are IntelAgent, an AI research assistant.
Current Date and Time: ${now}

## Step-by-step reasoning (REQUIRED)
Before calling any tool, reason silently through these steps:
1. Classify intent (see Intent Classification below).
2. Identify which tools are needed and in what order.
3. After each tool result, check: is the data sufficient? Are there errors or empty results?
4. Before calling render_dashboard, verify: chart.data is non-empty, all metrics have values, summary is populated.
Only proceed to the next step after completing the current one.

## Intent Classification
- MARKETING_INTEL: brand sentiment, competitor comparison, content trends, search rankings.
  → fetch_brand_sentiment → fetch_search_presence → fetch_content_trends
  → render_dashboard(metrics=[...], chart=..., table=..., layout="split")
  Use metrics for sentiment scores, chart (bar/radar) for brand comparisons, table for ranking data.

## Multi-turn context
- If a prior turn in this conversation already fetched data, reuse it for follow-up views (e.g. different chart type, filtered table) without re-fetching.
- Carry forward brand names, timeframes, and results from earlier turns unless the user explicitly changes them.

## Fallbacks (CRITICAL)
- If a tool returns {status: "insufficient_data"} or {status: "unavailable: ..."}: surface it in the summary as "Insufficient data for [platform/brand]" and set that metric value to "N/A". Never invent or estimate missing data.
- If ALL tools for a query return errors: call render_dashboard with summary explaining what failed and why; still include any partial data that succeeded.
- If chart.data would be empty after applying fallbacks: omit the chart param entirely rather than rendering an empty chart.

## Output Rules (CRITICAL)
- ALWAYS call render_dashboard when finished. It is the only output surface.
- Do NOT emit text outside of tool calls.
- summary: your full prose response to the user (2-3 sentences). ALWAYS populate this.
- PRO-ACTIVELY USE CHARTS: For numerical data, comparisons, or time-series, ALWAYS include a chart. You MUST explicitly set chart.type — never omit it. Pick from: "bar" (category comparison), "line" (time trend), "area" (volume trend), "pie" (part-of-whole), "radar" (multi-axis), "radial" (single gauge). For multi-brand sentiment: use "bar". For search rankings: use "bar". For single-brand sentiment breakdown: use "pie".
- Use metrics for KPI numbers. Use chart for visualizations. Use table for comparisons.
- layout="auto" always works — backend picks the best layout. Only set layout explicitly for "split".
- When showing sentiment results, ALWAYS include total_posts count per platform (e.g. "Based on 50 tweets" or "Analyzed 25 Reddit posts"). Surface this in the summary and/or as a metric.
`;

  const MAX_TURNS = 12;

  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const forceFinish = turn >= 8;
    console.log(`[Turn ${turn + 1}/${currentProviderType}]${forceFinish ? " FORCE FINISH" : ""}`);

    const { rawModelParts, toolCalls, textParts } = await activeProvider.generateContent(
      contents,
      functionDeclarations,
      systemInstruction,
      forceFinish
    );

    contents.push({ role: "model", parts: rawModelParts });

    if (!toolCalls || toolCalls.length === 0) {
      console.log(`[Turn ${turn + 1}] No tool calls. Text: "${textParts.slice(0, 100)}…"`);
      if (textParts) {
        setStatus("Rendering fallback…");
        try {
          await callMcpTool("render_dashboard", {
            title: "Research Result",
            summary: textParts,
          });
          renderDashboard();
          setStatus("Done.", "success");
        } catch (err) {
          setStatus(`Fallback Error: ${err.message}`, "error");
        }
      } else {
        console.log(`[Turn ${turn + 1}] Empty response, done.`);
        setStatus("Done.", "success");
      }
      return;
    }

    const toolResponseParts = [];
    let dashboardRendered = false;

    console.log(`[Turn ${turn + 1}] ${toolCalls.length} tool calls:`);
    for (const call of toolCalls) {
      const { name, args } = call;
      console.log(`  - ${name}(${JSON.stringify(args).slice(0, 60)}…)`);

      if (forceFinish && name !== "render_dashboard") {
        console.warn(`  → forceFinish active, skipping: ${name}`);
        toolResponseParts.push({
          functionResponse: { name, response: { content: { error: "Only render_dashboard allowed at this stage" } } },
        });
        continue;
      }

      let toolResult;
      try {
        toolResult = await callMcpTool(name, args);
      } catch (err) {
        toolResult = { error: err.message };
      }

      if (name === "render_dashboard") {
        if (toolResult?.status === "dashboard_ready") {
          console.log(`  → dashboard rendered`);
          renderDashboard();
        } else {
          console.warn(`  → dashboard render failed:`, toolResult);
          setStatus(`Dashboard error: ${toolResult?.status || JSON.stringify(toolResult)}`, "error");
        }
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

function appendChatMessage(text, type = "user") {
  const msg = document.createElement("div");
  msg.className = `chat-message ${type}`;
  msg.textContent = text;
  $chatHistory.insertBefore(msg, $chatHistory.firstChild);
  $chatHistory.scrollTop = $chatHistory.scrollHeight;
}

function updateChatButtonStates() {
  $undoBtn.disabled = userPromptHistory.length === 0;
  $clearBtn.disabled = userPromptHistory.length === 0;
}

function setStatus(msg, type = "") {
  $status.textContent = msg;
  $status.className = type;
}

function renderDashboard() {
  $emptyState.style.display = "none";
  $dashboardFrame.style.display = "block";
  const theme = document.documentElement.getAttribute("data-theme") || "dark";
  $dashboardFrame.src = `${DASHBOARD_URL}?theme=${theme}&t=${Date.now()}`;
}

function setServerStatus(online) {
  $dot.className = online ? "dot" : "dot offline";
  const noTools = online && mcpTools.length === 0;
  setStatus(
    !online
      ? "Server offline — run: python main.py"
      : noTools
        ? "Server connected but no tools loaded — check backend."
        : "Server connected. Enter a prompt."
  );
  $runBtn.disabled = !online || !isProviderReady() || noTools;
}

function updateProviderUI(type) {
  $ollamaSettings.style.display = type === "ollama" ? "flex" : "none";
  $geminiSettings.style.display = type === "gemini" ? "flex" : "none";
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

function loadSettings() {
  chrome.storage.local.get(
    [API_KEY_STORAGE, MCP_SERVER_URL_STORAGE, THEME_STORAGE, LLM_PROVIDER_STORAGE, GEMINI_MODEL_STORAGE, OLLAMA_URL_STORAGE, OLLAMA_MODEL_STORAGE, OLLAMA_THINKING_STORAGE],
    result => {
      geminiApiKey = result[API_KEY_STORAGE] || "";
      const providerType = result[LLM_PROVIDER_STORAGE] || "gemini";
      const geminiModel = result[GEMINI_MODEL_STORAGE] || DEFAULT_GEMINI_MODEL;
      const ollamaUrl = result[OLLAMA_URL_STORAGE] || DEFAULT_OLLAMA_URL;
      const ollamaModel = result[OLLAMA_MODEL_STORAGE] || DEFAULT_OLLAMA_MODEL;
      const ollamaThinking = !!result[OLLAMA_THINKING_STORAGE];

      $providerSelect.value = providerType;
      $geminiModelInput.value = geminiModel;
      $ollamaUrlInput.value = ollamaUrl;
      $ollamaModelInput.value = ollamaModel;
      $ollamaThinkingToggle.checked = ollamaThinking;
      updateProviderUI(providerType);

      if (geminiApiKey) {
        $apiKeyInput.value = "••••••••••••••••";
      } else if (providerType === "gemini") {
        setStatus("No API key — click ⚙️ to add one.");
      }

      initProvider(providerType, { apiKey: geminiApiKey, geminiModel, ollamaUrl, ollamaModel, ollamaThinking });

      const serverUrl = result[MCP_SERVER_URL_STORAGE] || "http://localhost:8000";
      $mcpUrlInput.value = serverUrl;
      MCP_URL = `${serverUrl.replace(/\/$/, "")}/mcp`;
      DASHBOARD_URL = `${serverUrl.replace(/\/$/, "")}/dashboard`;

      checkServer();
    }
  );
}

async function resetConnection() {
  mcpSessionId = null;
  conversationHistory = [];
  userPromptHistory = [];
  conversationCheckpoints = [];
  $chatHistory.innerHTML = "";
  setStatus("Resetting connection…");
  $dashboardFrame.style.display = "none";
  $emptyState.style.display = "flex";
  $runBtn.disabled = true;
  updateChatButtonStates();
  await checkServer();
}

$resetBtn.addEventListener("click", resetConnection);

$settingsBtn.addEventListener("click", () => {
  const visible = $settingsPanel.classList.toggle("visible");
  $settingsBtn.classList.toggle("active", visible);
});

$providerSelect.addEventListener("change", () => {
  updateProviderUI($providerSelect.value);
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
  const providerType = $providerSelect.value;
  const geminiModel = $geminiModelInput.value.trim() || DEFAULT_GEMINI_MODEL;
  const ollamaUrl = $ollamaUrlInput.value.trim() || DEFAULT_OLLAMA_URL;
  const ollamaModel = $ollamaModelInput.value.trim() || DEFAULT_OLLAMA_MODEL;
  const ollamaThinking = $ollamaThinkingToggle.checked;

  const settings = {
    [MCP_SERVER_URL_STORAGE]: serverUrl,
    [LLM_PROVIDER_STORAGE]: providerType,
    [GEMINI_MODEL_STORAGE]: geminiModel,
    [OLLAMA_URL_STORAGE]: ollamaUrl,
    [OLLAMA_MODEL_STORAGE]: ollamaModel,
    [OLLAMA_THINKING_STORAGE]: ollamaThinking,
  };

  if (key && !key.startsWith("•")) {
    geminiApiKey = key;
    settings[API_KEY_STORAGE] = key;
    $apiKeyInput.value = "••••••••••••••••";
  }

  const cleanUrl = serverUrl.replace(/\/$/, "");
  MCP_URL = `${cleanUrl}/mcp`;
  DASHBOARD_URL = `${cleanUrl}/dashboard`;

  // Re-init provider with new settings
  initProvider(providerType, { apiKey: geminiApiKey, geminiModel, ollamaUrl, ollamaModel, ollamaThinking });

  // Clear history when switching providers (incompatible formats mid-session)
  if (providerType !== currentProviderType) {
    conversationHistory = [];
    userPromptHistory = [];
    conversationCheckpoints = [];
    $chatHistory.innerHTML = "";
    updateChatButtonStates();
  }

  chrome.storage.local.set(settings, () => {
    $keyStatus.textContent = "Settings saved.";
    checkServer();
    setTimeout(() => { $keyStatus.textContent = ""; }, 2000);
  });
});

$runBtn.addEventListener("click", async () => {
  const prompt = $promptInput.value.trim();
  if (!prompt || !isProviderReady()) return;

  console.log(`[Before runAgent] history length:`, conversationHistory.length);
  $runBtn.disabled = true;
  try {
    await runAgent(prompt);
  } catch (err) {
    const checkpoint = conversationCheckpoints.pop();
    userPromptHistory.pop();
    if (checkpoint !== undefined) conversationHistory.length = checkpoint;
    if ($chatHistory.firstChild) $chatHistory.removeChild($chatHistory.firstChild);
    updateChatButtonStates();
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    console.log(`[After runAgent] history length:`, conversationHistory.length);
    $runBtn.disabled = !isProviderReady();
  }
});

$promptInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $runBtn.click();
  }
});

$promptInput.addEventListener("input", () => {
  $promptInput.style.height = "auto";
  $promptInput.style.height = Math.min($promptInput.scrollHeight, 200) + "px";
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== "local") return;
  if (changes[API_KEY_STORAGE]?.newValue) {
    geminiApiKey = changes[API_KEY_STORAGE].newValue;
    if (currentProviderType === "gemini") {
      initProvider("gemini", { apiKey: geminiApiKey });
    }
    setStatus("API key updated. Enter a prompt.");
  }
});

// ── Chat actions ──────────────────────────────────────────────────────────

$undoBtn.addEventListener("click", () => {
  if (userPromptHistory.length === 0) return;

  const lastPrompt = userPromptHistory.pop();
  const checkpoint = conversationCheckpoints.pop();
  $promptInput.value = lastPrompt;

  if ($chatHistory.firstChild) {
    $chatHistory.removeChild($chatHistory.firstChild);
  }

  conversationHistory.length = checkpoint;
  updateChatButtonStates();
});

$clearBtn.addEventListener("click", () => {
  if (confirm("Clear all chat history?")) {
    userPromptHistory = [];
    conversationHistory = [];
    conversationCheckpoints = [];
    $chatHistory.innerHTML = "";
    $promptInput.value = "";
    updateChatButtonStates();
  }
});

// ── Preset buttons ────────────────────────────────────────────────────────────

function setPreset(text) {
  $promptInput.value = text;
  $promptInput.dispatchEvent(new Event("input"));
  $promptInput.focus();
}

$presetSentiment.addEventListener("click", () =>
  setPreset("Compare sentiment for PharmEasy vs Tata 1mg vs Apollo 247 on Reddit and Twitter this week.")
);
$presetRadar.addEventListener("click", () =>
  setPreset("Compare PharmEasy vs Tata 1mg vs Apollo 247 across positive%, negative% and neutral% on Reddit as radar chart.")
);
$presetPie.addEventListener("click", () =>
  setPreset("What is the sentiment breakdown for PharmEasy on Reddit this month?")
);

// Read the rest of presets from the old file
$presetTrends?.addEventListener("click", () =>
  setPreset("What are the content trends for online pharmacy in India this week?")
);
$presetRankings.addEventListener("click", () =>
  setPreset("Check search rankings for PharmEasy, Tata 1mg, Apollo 247 for keywords: online pharmacy, medicine delivery, health app.")
);
$presetAnalysis.addEventListener("click", () =>
  setPreset("Full competitive analysis: sentiment, search rankings, and content trends for PharmEasy vs Tata 1mg vs Apollo 247.")
);

// ── Resizer ───────────────────────────────────────────────────────────────────

$resizer.addEventListener("mousedown", e => {
  isResizing = true;
  $resizer.classList.add("active");
  e.preventDefault();
});

document.addEventListener("mousemove", e => {
  if (!isResizing) return;
  const totalWidth = $mainView.offsetWidth;
  const offset = e.clientX - $mainView.getBoundingClientRect().left;
  const pct = Math.min(Math.max((offset / totalWidth) * 100, 20), 80);
  $dashboardPanel.style.flex = `0 0 ${pct}%`;
  $chatPanel.style.flex = `0 0 ${100 - pct}%`;
});

document.addEventListener("mouseup", () => {
  if (isResizing) {
    isResizing = false;
    $resizer.classList.remove("active");
  }
});

// ── Bootstrap ─────────────────────────────────────────────────────────────────

loadTheme();
loadSettings();
