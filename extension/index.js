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
const $presetTrends = document.getElementById("preset-trends");
const $presetRankings = document.getElementById("preset-rankings");
const $presetAnalysis = document.getElementById("preset-analysis");

let mcpTools = [];
let geminiApiKey = "";
let mcpSessionId = null;
let ai = null;
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
  console.log(`[Agent Init] After push, history length: ${contents.length}, user turns: ${contents.filter(t => t.role === "user").length}`);

  const now = new Date().toLocaleString();
  const systemInstruction = `You are IntelAgent, an AI research assistant.
Current Date and Time: ${now}

Pick tools based on the user's intent.

Intent classification:
- MARKETING_INTEL: brand sentiment, competitor comparison, content trends, search rankings.
  → fetch_brand_sentiment → fetch_search_presence → fetch_content_trends
  → render_dashboard(metrics=[...], chart=..., table=..., layout="split")
  Use metrics for sentiment scores, chart (bar/radar) for brand comparisons, table for ranking data.

Rules (CRITICAL):
- ALWAYS call render_dashboard when finished. It is the only output surface.
- PRO-ACTIVELY USE CHARTS: If you are dealing with numerical data, comparisons, or time-series, ALWAYS include a chart in render_dashboard. You MUST explicitly set chart.type — never omit it. Pick from: "bar" (category comparison), "line" (time trend), "area" (volume trend), "pie" (part-of-whole), "radar" (multi-axis), "radial" (single gauge). For multi-brand sentiment: use "bar". For search rankings: use "bar". For single-brand sentiment breakdown: use "pie".
- Do NOT emit text outside of tool calls.
- summary: your full prose response to the user (2-3 sentences). ALWAYS populate this.
- Use metrics for KPI numbers. Use chart for visualizations. Use table for comparisons.
- layout="auto" always works — backend picks the best layout. Only set layout explicitly for "split".
- When showing sentiment results, ALWAYS include total_posts count per platform (e.g. "Based on 50 tweets" or "Analyzed 25 Reddit posts"). Surface this in the summary and/or as a metric.
`;

  const MAX_TURNS = 12;

  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const forceFinish = turn >= 8;
    console.log(`[Turn ${turn + 1}] Calling Gemini${forceFinish ? " (FORCE FINISH)" : ""}…`);
    const response = await ai.models.generateContent({
      model: MODEL,
      contents,
      config: {
        systemInstruction,
        tools: [
          { functionDeclarations: functionDeclarations.length ? functionDeclarations : [] },
          ...(forceFinish ? [] : [{ googleSearch: {} }]),
        ],
        toolConfig: {
          functionCallingConfig: forceFinish
            ? { mode: "ANY", allowedFunctionNames: ["render_dashboard"] }
            : { mode: "AUTO" },
          ...(!forceFinish && {
            googleSearchRetrieval: {
              dynamicRetrievalConfig: { mode: "DYNAMIC", dynamicThreshold: 0.3 },
            },
            includeServerSideToolInvocations: true,
          }),
        },
        generationConfig: { temperature: 0 },
      },
    });

    const candidate = response.candidates?.[0];
    if (!candidate) throw new Error("No candidates in Gemini response");

    const parts = candidate.content?.parts || [];
    contents.push({ role: "model", parts });

    const toolCalls = response.functionCalls;

    if (!toolCalls || toolCalls.length === 0) {
      const textResponse = parts.map(p => p.text || "").join("\n").trim();
      console.log(`[Turn ${turn + 1}] No tool calls. Text response: "${textResponse.slice(0, 100)}…"`);
      if (textResponse) {
        setStatus("Rendering fallback…");
        try {
          await callMcpTool("render_dashboard", {
            title: "Research Result",
            summary: textResponse
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
        console.warn(`  → forceFinish active, skipping disallowed tool: ${name}`);
        toolResponseParts.push({
          functionResponse: { name, response: { content: { error: "Only render_dashboard allowed at this stage" } } }
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
  // Cache-bust so iframe re-fetches latest /dashboard HTML
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
  $runBtn.disabled = !online || !geminiApiKey || noTools;
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

  console.log(`[Before runAgent] conversationHistory length:`, conversationHistory.length);
  $runBtn.disabled = true;
  try {
    await runAgent(prompt);
  } catch (err) {
    // Restore fully to pre-prompt state using the checkpoint runAgent just pushed
    const checkpoint = conversationCheckpoints.pop();
    userPromptHistory.pop();
    if (checkpoint !== undefined) conversationHistory.length = checkpoint;
    if ($chatHistory.firstChild) $chatHistory.removeChild($chatHistory.firstChild);
    updateChatButtonStates();
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
  if (area === "local" && changes[API_KEY_STORAGE]?.newValue) {
    geminiApiKey = changes[API_KEY_STORAGE].newValue;
    initGemini(geminiApiKey);
    $runBtn.disabled = false;
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
  setPreset("Compare sentiment for PharmEasy vs Tata 1mg vs Apollo Pharmacy on Reddit and Twitter this week.")
);
// $presetTrends.addEventListener("click", () =>
//   setPreset("Show Google Trends interest for 'online pharmacy' across tier1 and tier2 Indian cities this month.")
// );
$presetRankings.addEventListener("click", () =>
  setPreset("Check search rankings for PharmEasy vs Tata 1mg vs Apollo Pharmacy vs Netmeds for 'buy medicines online india', 'medicine delivery app india', 'book lab test india', 'lab tests at home india', and 'order medicines online india'.")
);
$presetAnalysis.addEventListener("click", () =>
  setPreset("Run a full competitive analysis for PharmEasy vs Tata 1mg vs Apollo Pharmacy: sentiment on Reddit and Twitter, and search rankings for 'buy medicines online india'.")
);

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

updateChatButtonStates();
loadTheme();
loadSettings();
