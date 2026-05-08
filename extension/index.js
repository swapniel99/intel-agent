import { GoogleGenAI } from "./genai.js";
import { GeminiProvider } from "./providers/gemini-provider.js";
import { OllamaProvider } from "./providers/ollama-provider.js";

let MCP_URL = "http://localhost:8000/mcp";
const API_KEY_STORAGE = "gemini_api_key";
const MCP_SERVER_URL_STORAGE = "mcp_server_url";
const THEME_STORAGE = "theme";
const LLM_PROVIDER_STORAGE = "llm_provider";
const GEMINI_MODEL_STORAGE = "gemini_model";
const OLLAMA_URL_STORAGE = "ollama_url";
const OLLAMA_MODEL_STORAGE = "ollama_model";
const OLLAMA_THINKING_STORAGE = "ollama_reasoning_effort";
const GEMINI_THINKING_STORAGE = "gemini_thinking";
const DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview";
const DEFAULT_OLLAMA_URL = "http://localhost:11434";
const DEFAULT_OLLAMA_MODEL = "gemma4:e2b";

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
const $providerSelect = document.getElementById("provider-select");
const $geminiSettings = document.getElementById("gemini-settings");
const $ollamaSettings = document.getElementById("ollama-settings");
const $geminiModelInput = document.getElementById("gemini-model-input");
const $ollamaUrlInput = document.getElementById("ollama-url-input");
const $ollamaModelInput = document.getElementById("ollama-model-input");
const $ollamaThinkingSelect = document.getElementById("ollama-thinking-select");
const $geminiThinkingSelect = document.getElementById("gemini-thinking-select");
const $presetHeadlines = document.getElementById("preset-headlines");
const $presetAi = document.getElementById("preset-ai");
const $presetLibrary = document.getElementById("preset-library");
const $presetDigest = document.getElementById("preset-digest");
const $presetCompare = document.getElementById("preset-compare");

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

// ── Provider helpers ──────────────────────────────────────────────────────────

function initProvider(type, { apiKey, geminiModel, geminiThinking, ollamaUrl, ollamaModel, ollamaThinking } = {}) {
  currentProviderType = type;
  if (type === "ollama") {
    activeProvider = new OllamaProvider(
      ollamaUrl || DEFAULT_OLLAMA_URL,
      ollamaModel || DEFAULT_OLLAMA_MODEL,
      ollamaThinking || ""
    );
  } else {
    if (apiKey) {
      ai = new GoogleGenAI({ apiKey });
      activeProvider = new GeminiProvider(ai, geminiModel || DEFAULT_GEMINI_MODEL, geminiThinking || null);
    } else {
      activeProvider = null;
    }
  }
}

function isProviderReady() {
  if (currentProviderType === "ollama") return activeProvider !== null;
  return !!geminiApiKey && activeProvider !== null;
}

function mcpToolsToFunctionDeclarations(tools) {
  return tools.map(t => ({
    name: t.name,
    description: t.description || "",
    parameters: t.inputSchema || { type: "object", properties: {} },
  }));
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

Pick tools based on the user's intent.

Intent classification:
- HYBRID_RESEARCH: latest info + saved knowledge.
  → search local library → fetch internet sources OR web search → dedupe & summarize → merge results → save new articles → render dashboard
- ARTICLE_CURATION: list/feed/digest of new articles.
  → fetch internet sources → dedupe & summarize → save new articles → render dashboard
- LIBRARY_MANAGEMENT: browse, search, or clean local collection.
  → read local library → render dashboard
- DATA_ANALYSIS: KPIs, comparisons, benchmarks, trends, rankings, market data, any numerical output.
  → gather data (web search / internet fetch) → identify metrics → render dashboard with chart + metrics

Rules (CRITICAL):
- ALWAYS render the dashboard when finished. It is the only output surface.
- ALWAYS gather data using tools BEFORE rendering. Never render from training knowledge alone.
- Dashboard MUST include at least one of: cards, metrics, chart, or table. summary-only renders are FORBIDDEN.
- PRO-ACTIVELY USE CHARTS: If you have numerical data, comparisons, or time-series, ALWAYS include a chart.
- Do NOT emit text outside of tool calls.
- summary: 2-3 sentence prose ONLY. NEVER put data, lists, or markdown in summary. All gathered data MUST go into cards, metrics, chart, or table.
- Use cards for article feeds. Use metrics for KPI numbers. Use chart for visualizations. Use table for comparisons.
- layout="auto" always works. Only set layout="split" for side-by-side chart + metrics.
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
            summary: textParts
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

      let toolResult;
      try {
        toolResult = await callMcpTool(name, args);
      } catch (err) {
        toolResult = { error: err.message };
      }

      if (name === "render_dashboard" && toolResult?.status === "dashboard_ready") {
        console.log(`  → dashboard rendered`);
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
  $runBtn.disabled = !online || !isProviderReady();
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
  chrome.storage.local.get([
    API_KEY_STORAGE, MCP_SERVER_URL_STORAGE,
    LLM_PROVIDER_STORAGE, GEMINI_MODEL_STORAGE, GEMINI_THINKING_STORAGE,
    OLLAMA_URL_STORAGE, OLLAMA_MODEL_STORAGE, OLLAMA_THINKING_STORAGE,
  ], result => {
    const provider = result[LLM_PROVIDER_STORAGE] || "gemini";
    currentProviderType = provider;
    $providerSelect.value = provider;

    if (provider === "ollama") {
      $geminiSettings.style.display = "none";
      $ollamaSettings.style.display = "flex";
      const ollamaUrl = result[OLLAMA_URL_STORAGE] || DEFAULT_OLLAMA_URL;
      const ollamaModel = result[OLLAMA_MODEL_STORAGE] || DEFAULT_OLLAMA_MODEL;
      const ollamaThinking = result[OLLAMA_THINKING_STORAGE] || "";
      $ollamaUrlInput.value = ollamaUrl;
      $ollamaModelInput.value = ollamaModel;
      $ollamaThinkingSelect.value = ollamaThinking;
      initProvider("ollama", { ollamaUrl, ollamaModel, ollamaThinking });
    } else {
      $geminiSettings.style.display = "flex";
      $ollamaSettings.style.display = "none";
      geminiApiKey = result[API_KEY_STORAGE] || "";
      const geminiModel = result[GEMINI_MODEL_STORAGE] || DEFAULT_GEMINI_MODEL;
      const geminiThinking = result[GEMINI_THINKING_STORAGE] || "";
      $geminiModelInput.value = geminiModel;
      $geminiThinkingSelect.value = geminiThinking;
      if (geminiApiKey) {
        $apiKeyInput.value = "••••••••••••••••";
        initProvider("gemini", { apiKey: geminiApiKey, geminiModel, geminiThinking });
      } else {
        setStatus("No API key — click ⚙️ to add one.");
      }
    }

    const serverUrl = result[MCP_SERVER_URL_STORAGE] || "http://localhost:8000";
    $mcpUrlInput.value = serverUrl;
    MCP_URL = `${serverUrl.replace(/\/$/, "")}/mcp`;
    DASHBOARD_URL = `${serverUrl.replace(/\/$/, "")}/dashboard`;

    $runBtn.disabled = !isProviderReady();
    checkServer();
  });
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

$providerSelect.addEventListener("change", () => {
  const provider = $providerSelect.value;
  if (provider === "ollama") {
    $geminiSettings.style.display = "none";
    $ollamaSettings.style.display = "flex";
  } else {
    $geminiSettings.style.display = "flex";
    $ollamaSettings.style.display = "none";
  }
});

$saveSettingsBtn.addEventListener("click", () => {
  const provider = $providerSelect.value;
  const serverUrl = $mcpUrlInput.value.trim() || "http://localhost:8000";
  const cleanUrl = serverUrl.replace(/\/$/, "");
  MCP_URL = `${cleanUrl}/mcp`;
  DASHBOARD_URL = `${cleanUrl}/dashboard`;

  const settings = {
    [MCP_SERVER_URL_STORAGE]: serverUrl,
    [LLM_PROVIDER_STORAGE]: provider,
  };

  if (provider === "ollama") {
    const ollamaUrl = $ollamaUrlInput.value.trim() || DEFAULT_OLLAMA_URL;
    const ollamaModel = $ollamaModelInput.value.trim() || DEFAULT_OLLAMA_MODEL;
    const ollamaThinking = $ollamaThinkingSelect.value;
    settings[OLLAMA_URL_STORAGE] = ollamaUrl;
    settings[OLLAMA_MODEL_STORAGE] = ollamaModel;
    settings[OLLAMA_THINKING_STORAGE] = ollamaThinking;
    initProvider("ollama", { ollamaUrl, ollamaModel, ollamaThinking });
  } else {
    const key = $apiKeyInput.value.trim();
    const geminiModel = $geminiModelInput.value.trim() || DEFAULT_GEMINI_MODEL;
    const geminiThinking = $geminiThinkingSelect.value;
    settings[GEMINI_MODEL_STORAGE] = geminiModel;
    settings[GEMINI_THINKING_STORAGE] = geminiThinking;
    if (key && !key.startsWith("•")) {
      geminiApiKey = key;
      settings[API_KEY_STORAGE] = key;
      $apiKeyInput.value = "••••••••••••••••";
      initProvider("gemini", { apiKey: geminiApiKey, geminiModel, geminiThinking });
    } else {
      initProvider("gemini", { apiKey: geminiApiKey, geminiModel, geminiThinking });
    }
  }

  chrome.storage.local.set(settings, () => {
    $keyStatus.textContent = "Settings saved.";
    $runBtn.disabled = !isProviderReady();
    setTimeout(() => { $keyStatus.textContent = ""; }, 2000);
    checkServer();
  });
});

$runBtn.addEventListener("click", async () => {
  const prompt = $promptInput.value.trim();
  if (!prompt || !isProviderReady()) return;

  console.log(`[Before runAgent] conversationHistory length:`, conversationHistory.length);
  $runBtn.disabled = true;
  try {
    await runAgent(prompt);
  } catch (err) {
    conversationHistory.pop();
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    console.log(`[After runAgent] conversationHistory length:`, conversationHistory.length);
    $runBtn.disabled = false;
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
  if (area === "local" && changes[API_KEY_STORAGE]?.newValue && currentProviderType === "gemini") {
    geminiApiKey = changes[API_KEY_STORAGE].newValue;
    const geminiModel = $geminiModelInput.value.trim() || DEFAULT_GEMINI_MODEL;
    const geminiThinking = $geminiThinkingSelect.value;
    initProvider("gemini", { apiKey: geminiApiKey, geminiModel, geminiThinking });
    $runBtn.disabled = !isProviderReady();
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

// ── Resizable panels ──────────────────────────────────────────────────────────

$resizer.addEventListener("mousedown", () => {
  isResizing = true;
  $resizer.classList.add("active");
});

document.addEventListener("mousemove", (e) => {
  if (!isResizing) return;

  const mainRect = $mainView.getBoundingClientRect();
  const newDashWidth = e.clientX - mainRect.left;
  const minDash = mainRect.width * 0.3;
  const maxDash = mainRect.width * 0.8;
  const clamped = Math.max(minDash, Math.min(maxDash, newDashWidth));

  const dashPercent = (clamped / mainRect.width) * 100;
  const chatPercent = 100 - dashPercent - 0.5;

  $dashboardPanel.style.flex = `0 0 ${dashPercent}%`;
  $chatPanel.style.flex = `0 0 ${chatPercent}%`;
});

document.addEventListener("mouseup", () => {
  isResizing = false;
  $resizer.classList.remove("active");
});

// ── Preset buttons ────────────────────────────────────────────────────────────

const PRESETS = {
  headlines: 'Fetch the top 6 latest tech articles from all sources (HN, Dev.to, Reddit) and render a dashboard with article cards.',
  ai: 'Fetch the latest articles on AI and Large Language Models from all sources, save new ones to the library, and render a dashboard with a bar chart showing article counts by source.',
  library: 'Show all saved articles in the local library as a dashboard with article cards.',
  digest: 'Fetch the top trending tech articles from this week across all sources and create a summary dashboard with key highlights and a chart.',
  compare: 'Compare recent coverage of React vs Vue vs Angular by fetching articles on each topic, then render a dashboard with a bar chart comparing article counts and a summary.',
};

function firePreset(key) {
  $promptInput.value = PRESETS[key];
  $promptInput.style.height = "auto";
  $promptInput.style.height = Math.min($promptInput.scrollHeight, 200) + "px";
  $runBtn.click();
}

$presetHeadlines.addEventListener("click", () => firePreset("headlines"));
$presetAi.addEventListener("click", () => firePreset("ai"));
$presetLibrary.addEventListener("click", () => firePreset("library"));
$presetDigest.addEventListener("click", () => firePreset("digest"));
$presetCompare.addEventListener("click", () => firePreset("compare"));

updateChatButtonStates();
loadTheme();
loadSettings();
