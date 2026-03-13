/**
 * Background script Firefox (Manifest V2).
 * Gère le cache local (browser.storage.local), les appels à l'API GO Evolution,
 * et l'icône dynamique par onglet.
 */

const LOG = (...args) => console.log("[GO-Evo BG]", ...args);

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 h

const ICON_PATHS = {
  grey:   "icons/icon-grey.svg",
  yellow: "icons/icon-yellow.svg",
  green:  "icons/icon-green.svg",
  red:    "icons/icon-red.svg",
  orange: "icons/icon-orange.svg",
};

function setTabIcon(tabId, state) {
  LOG(`icon → ${state} (tab ${tabId})`);
  browser.browserAction.setIcon({ tabId, path: ICON_PATHS[state] });
}

// ---------------------------------------------------------------------------
// Cache
// ---------------------------------------------------------------------------

async function getCached(goId) {
  const key = `cache_${goId}`;
  const result = await browser.storage.local.get(key);
  const entry = result[key];
  if (entry && Date.now() - entry.timestamp < CACHE_TTL_MS) {
    LOG(`cache HIT for ${goId}`);
    return entry.data;
  }
  LOG(`cache MISS for ${goId}`);
  return null;
}

async function setCached(goId, data) {
  const key = `cache_${goId}`;
  await browser.storage.local.set({ [key]: { data, timestamp: Date.now() } });
  LOG(`cache SET for ${goId}`);
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

async function fetchTermDiff(goId, tabId) {
  const settings = await browser.storage.local.get(["apiUrl", "cacheEnabled"]);
  const apiUrl = settings.apiUrl || "http://localhost:8000";
  const cacheEnabled = settings.cacheEnabled !== false;

  if (cacheEnabled) {
    const cached = await getCached(goId);
    if (cached) {
      setTabIcon(tabId, "green");
      return cached;
    }
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
  if (cacheEnabled) await setCached(goId, data);

  setTabIcon(tabId, "green");
  return data;
}

// ---------------------------------------------------------------------------
// Message listener
// ---------------------------------------------------------------------------

browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
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
