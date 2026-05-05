import { GoogleGenAI } from "./genai.js";

const MCP_URL = "http://localhost:8000/mcp";
const MODEL = "gemini-3.1-flash-lite-preview";
const API_KEY_STORAGE = "gemini_api_key";

const $dot = document.getElementById("server-dot");
const $status = document.getElementById("status-bar");
const $log = document.getElementById("log-section");
const $runBtn = document.getElementById("run-btn");
const $promptInput = document.getElementById("prompt-input");
const $apiKeyInput = document.getElementById("api-key-input");
const $saveKeyBtn = document.getElementById("save-key-btn");
const $frame = document.getElementById("prefab-frame");
const $emptyState = document.getElementById("empty-state");

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

  const res = await fetch(MCP_URL, {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id: Date.now(), method, params }),
  });

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

  const functionDeclarations = mcpToolsToFunctionDeclarations(mcpTools);

  const contents = [
    { role: "user", parts: [{ text: userPrompt }] },
  ];

  const systemInstruction = `You are AgentCurator, an AI research assistant.
You MUST always complete the full pipeline using the available tools in this order:
1. Call fetch_tech_news to get articles
2. Call manage_local_library with action="check_duplicates" to filter seen articles
3. Call manage_local_library with action="save_new" to save novel articles
4. Call render_prefab_dashboard with the articles to render the UI

For render_prefab_dashboard, classify the user's topic into the single best-matching category from this list and pass that category name as the topic argument:
medical, security, rust, python, ai, web, cloud, data, game, crypto
If the topic fits none of these, pick the closest one by domain (e.g. "kubernetes" → cloud, "pytorch" → ai, "solidity" → crypto). Never pass the full prompt as topic.

You MUST call render_prefab_dashboard as the final step — never skip it, never describe the dashboard in text instead of rendering it.`;

  const MAX_TURNS = 12;

  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const response = await ai.models.generateContent({
      model: MODEL,
      contents,
      config: {
        systemInstruction,
        tools: functionDeclarations.length
          ? [{ functionDeclarations }]
          : undefined,
        generationConfig: { temperature: 0.2 },
      },
    });

    const candidate = response.candidates?.[0];
    if (!candidate) throw new Error("No candidates in Gemini response");

    const parts = candidate.content?.parts || [];
    contents.push({ role: "model", parts });

    const toolCalls = response.functionCalls;

    if (!toolCalls || toolCalls.length === 0) {
      setStatus("Done.", "success");
      const text = response.text;
      if (text) appendLog(`Gemini: ${text}`);
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

      if (name === "render_prefab_dashboard" && typeof toolResult === "string") {
        renderPrefab(toolResult);
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

function renderPrefab(_html) {
  $emptyState.style.display = "none";
  // Load from backend endpoint — avoids srcdoc/blob CSP issues with Prefab's CDN module chunks
  $frame.removeAttribute("srcdoc");
  $frame.src = `http://localhost:8000/dashboard?t=${Date.now()}`;
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
      $apiKeyInput.value = "••••••••••••••••";
      initGemini(geminiApiKey);
    }
    $runBtn.disabled = !geminiApiKey;
  });
}

$saveKeyBtn.addEventListener("click", () => {
  const key = $apiKeyInput.value.trim();
  if (!key || key.startsWith("•")) return;
  geminiApiKey = key;
  initGemini(key);
  chrome.storage.local.set({ [API_KEY_STORAGE]: key }, () => {
    $apiKeyInput.value = "••••••••••••••••";
    setStatus("API key saved.", "success");
    $runBtn.disabled = false;
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

loadApiKey();
checkServer();
