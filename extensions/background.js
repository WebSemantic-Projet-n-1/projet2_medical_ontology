/**
 * Background/service worker script shared between Firefox (Manifest V2)
 * and Chrome (Manifest V3 service worker).
 * Gère le cache local (browser.storage.local), les appels à l'API GO Evolution,
 * et l'icône dynamique par onglet. Doit rester compatible avec les contextes MV2 et MV3.
 */

// Cross-browser extension API wrapper
const ext = globalThis.browser ?? globalThis.chrome;

const LOG = (...args) => console.log("[GO-Evo BG]", ...args);

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 h

// djb2 hash — used to namespace cache keys by apiUrl without storing the full URL
function hashStr(s) {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = (h * 33) ^ s.charCodeAt(i);
  return (h >>> 0).toString(36);
}

const FIREFOX_ICON_PATHS = {
  grey:   "icons/icon-grey.svg",
  yellow: "icons/icon-yellow.svg",
  green:  "icons/icon-green.svg",
  red:    "icons/icon-red.svg",
  orange: "icons/icon-orange.svg",
};

const CHROME_ICON_PATHS = {
  grey: "icons/icon-grey.png",
  yellow: "icons/icon-yellow.png",
  green: "icons/icon-green.png",
  red: "icons/icon-red.png",
  orange: "icons/icon-orange.png",
};

// Abstraction for toolbar/action API across Firefox MV2/MV3 and Chrome MV3
const toolbarAction = (ext && (ext.action || ext.browserAction)) || null;

function setTabIcon(tabId, state) {
  if (typeof tabId !== "number") {
    LOG(`icon → ${state} (no valid tabId, skipping setIcon)`);
    return;
  }
  if (!toolbarAction || typeof toolbarAction.setIcon !== "function") {
    LOG(`icon → ${state} (no toolbar action API available, skipping setIcon)`);
    return;
  }
  LOG(`icon → ${state} (tab ${tabId})`);
  const paths = globalThis.browser ? FIREFOX_ICON_PATHS : CHROME_ICON_PATHS;
  toolbarAction.setIcon({ tabId, path: paths[state] });
}

// ---------------------------------------------------------------------------
// Cache
// ---------------------------------------------------------------------------

async function getCached(goId, apiUrl) {
  const key = `cache_${hashStr(apiUrl)}_${goId}`;
  const result = await ext.storage.local.get(key);
  const entry = result[key];
  if (entry && Date.now() - entry.timestamp < CACHE_TTL_MS) {
    LOG(`cache HIT for ${goId}`);
    return entry.data;
  }
  LOG(`cache MISS for ${goId}`);
  return null;
}

async function setCached(goId, data, apiUrl) {
  const key = `cache_${hashStr(apiUrl)}_${goId}`;
  await ext.storage.local.set({ [key]: { data, timestamp: Date.now() } });
  LOG(`cache SET for ${goId}`);
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function fetchTermDiff(goId, tabId) {
  const settings = await ext.storage.local.get(["apiUrl"]);
  const apiUrl = settings.apiUrl || "http://localhost:8000";

  const cached = await getCached(goId, apiUrl);
  if (cached) {
    setTabIcon(tabId, "green");
    return cached;
  }

  setTabIcon(tabId, "yellow");

  const url = `${apiUrl}/api/term/${encodeURIComponent(goId)}/diff`;
  LOG(`fetch ${url}`);

  const resp = await fetch(url);
  LOG(`response ${resp.status} for ${goId}`);

  if (resp.status === 404) {
    setTabIcon(tabId, "orange");
    return { notFound: true };
  }

  if (!resp.ok) {
    setTabIcon(tabId, "red");
    throw new Error(`API ${resp.status}`);
  }

  const data = await resp.json();
  await setCached(goId, data, apiUrl);

  setTabIcon(tabId, "green");
  return data;
}

// ---------------------------------------------------------------------------
// Message listener
// ---------------------------------------------------------------------------

ext.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "getTermDiff" && message.goId) {
    const tabId = sender.tab?.id;
    LOG(`received getTermDiff for ${message.goId} (tab ${tabId})`);

    if (tabId) setTabIcon(tabId, "yellow");

    fetchTermDiff(message.goId, tabId)
      .then((data) => sendResponse(data))
      .catch((err) => {
        LOG(`error for ${message.goId}: ${err.message}`);
        if (tabId) setTabIcon(tabId, "red");
        sendResponse({ error: err.message });
      });
    return true;
  }
});
