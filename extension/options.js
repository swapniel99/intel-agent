const API_KEY_STORAGE = "gemini_api_key";
const $input = document.getElementById("api-key-input");
const $btn = document.getElementById("save-btn");
const $status = document.getElementById("status");

chrome.storage.local.get([API_KEY_STORAGE], result => {
  if (result[API_KEY_STORAGE]) $input.value = "••••••••••••••••";
});

$btn.addEventListener("click", () => {
  const key = $input.value.trim();
  if (!key || key.startsWith("•")) return;
  chrome.storage.local.set({ [API_KEY_STORAGE]: key }, () => {
    $input.value = "••••••••••••••••";
    $status.textContent = "Saved.";
    setTimeout(() => { $status.textContent = ""; }, 2000);
  });
});
