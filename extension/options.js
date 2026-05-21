import { storage, DEFAULT_SERVER_URL } from "./storage.js";

const API_KEY_STORAGE = "gemini_api_key";
const MCP_SERVER_URL_STORAGE = "mcp_server_url";

const $apiKeyInput = document.getElementById("api-key-input");
const $mcpUrlInput = document.getElementById("mcp-url-input");
const $btn = document.getElementById("save-btn");
const $status = document.getElementById("status");

storage.get([API_KEY_STORAGE, MCP_SERVER_URL_STORAGE], result => {
  if (result[API_KEY_STORAGE]) $apiKeyInput.value = "••••••••••••••••";
  $mcpUrlInput.value = result[MCP_SERVER_URL_STORAGE] || DEFAULT_SERVER_URL;
});

$btn.addEventListener("click", () => {
  const key = $apiKeyInput.value.trim();
  const serverUrl = $mcpUrlInput.value.trim() || DEFAULT_SERVER_URL;

  const settings = {
    [MCP_SERVER_URL_STORAGE]: serverUrl
  };

  if (key && !key.startsWith("•")) {
    settings[API_KEY_STORAGE] = key;
    $apiKeyInput.value = "••••••••••••••••";
  }

  storage.set(settings, () => {
    $status.textContent = "Settings saved.";
    setTimeout(() => { $status.textContent = ""; }, 2000);
  });
});
