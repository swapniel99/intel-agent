// Environment shim — lets the UI run both as a Chrome extension and as a
// plain hosted website (served by the backend at the server root).
//
// As an extension, settings live in chrome.storage.local.
// As a website, chrome.* is undefined — fall back to window.localStorage.

const isExtension = typeof chrome !== "undefined" && !!chrome.storage;

export const storage = isExtension
  ? chrome.storage.local
  : {
      get(keys, cb) {
        const list = Array.isArray(keys)
          ? keys
          : typeof keys === "string"
            ? [keys]
            : Object.keys(keys || {});
        const out = {};
        for (const k of list) {
          const v = localStorage.getItem(k);
          if (v !== null) {
            try { out[k] = JSON.parse(v); } catch { out[k] = v; }
          }
        }
        cb(out);
      },
      set(obj, cb) {
        for (const [k, v] of Object.entries(obj)) {
          localStorage.setItem(k, JSON.stringify(v));
        }
        cb && cb();
      },
    };

// localStorage has no in-tab change event — no-op listener off-extension.
export const storageOnChanged = isExtension
  ? chrome.storage.onChanged
  : { addListener() {} };

// Default backend: same origin when hosted as a website, localhost when
// packaged as an extension (chrome-extension:// origin can't host the API).
export const DEFAULT_SERVER_URL = isExtension
  ? "http://localhost:8000"
  : window.location.origin;
