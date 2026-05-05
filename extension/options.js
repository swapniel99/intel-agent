const API_KEY_STORAGE = "gemini_api_key";
const MCP_SERVER_URL_STORAGE = "mcp_server_url";

const $apiKeyInput = document.getElementById("api-key-input");
const $mcpUrlInput = document.getElementById("mcp-url-input");
const $btn = document.getElementById("save-btn");
const $status = document.getElementById("status");

chrome.storage.local.get([API_KEY_STORAGE, MCP_SERVER_URL_STORAGE], result => {
  if (result[API_KEY_STORAGE]) $apiKeyInput.value = "••••••••••••••••";
  $mcpUrlInput.value = result[MCP_SERVER_URL_STORAGE] || "http://localhost:8000";
});

$btn.addEventListener("click", () => {
  const key = $apiKeyInput.value.trim();
  const serverUrl = $mcpUrlInput.value.trim() || "http://localhost:8000";

  const settings = {
    [MCP_SERVER_URL_STORAGE]: serverUrl
  };

  if (key && !key.startsWith("•")) {
    settings[API_KEY_STORAGE] = key;
    $apiKeyInput.value = "••••••••••••••••";
  }

  chrome.storage.local.set(settings, () => {
    $status.textContent = "Settings saved.";
    setTimeout(() => { $status.textContent = ""; }, 2000);
  });
});
