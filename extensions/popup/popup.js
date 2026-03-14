/**
 * Popup — sauvegarde et chargement des options GO Evolution.
 * Compatible Firefox (browser.*) et Chrome (chrome.*).
 */

/** Cross-browser extension API handle. */
const ext = globalThis.browser ?? globalThis.chrome;

/**
 * True when running in Firefox (browser.*), which natively returns Promises.
 * False when running in Chrome MV2 (chrome.*), which uses callbacks.
 */
const USE_PROMISE_API = !!globalThis.browser;

/**
 * Promisified wrapper for ext.storage.local.get.
 * Branches by API type so the storage call is issued exactly once.
 * @param {string[]|null} keys
 * @returns {Promise<object>}
 */
function storageGet(keys) {
  if (USE_PROMISE_API) return ext.storage.local.get(keys);
  return new Promise((resolve, reject) => {
    ext.storage.local.get(keys, (data) => {
      if (ext.runtime.lastError) reject(ext.runtime.lastError);
      else resolve(data);
    });
  });
}

/**
 * Promisified wrapper for ext.storage.local.set.
 * Branches by API type so the storage call is issued exactly once.
 * @param {object} items
 * @returns {Promise<void>}
 */
function storageSet(items) {
  if (USE_PROMISE_API) return ext.storage.local.set(items);
  return new Promise((resolve, reject) => {
    ext.storage.local.set(items, () => {
      if (ext.runtime.lastError) reject(ext.runtime.lastError);
      else resolve();
    });
  });
}

/**
 * Promisified wrapper for ext.storage.local.remove.
 * Branches by API type so the storage call is issued exactly once.
 * @param {string[]} keys
 * @returns {Promise<void>}
 */
function storageRemove(keys) {
  if (USE_PROMISE_API) return ext.storage.local.remove(keys);
  return new Promise((resolve, reject) => {
    ext.storage.local.remove(keys, () => {
      if (ext.runtime.lastError) reject(ext.runtime.lastError);
      else resolve();
    });
  });
}

const DEFAULTS = {
  domain: "0006281",
  apiUrl: "http://localhost:8000",
};

document.addEventListener("DOMContentLoaded", async () => {
  const domainEl      = document.getElementById("domain");
  const apiUrlEl      = document.getElementById("apiUrl");
  const saveBtn       = document.getElementById("save");
  const clearCacheBtn = document.getElementById("clearCache");
  const statsEl       = document.getElementById("stats");
  const apiBadgeEl    = document.getElementById("api-badge");

  const stored = await storageGet(Object.keys(DEFAULTS));
  domainEl.value = stored.domain  || DEFAULTS.domain;
  apiUrlEl.value = stored.apiUrl  || DEFAULTS.apiUrl;

  loadStats(stored.apiUrl || DEFAULTS.apiUrl, domainEl.value, statsEl, apiBadgeEl);

  saveBtn.addEventListener("click", async () => {
    await storageSet({
      domain: domainEl.value,
      apiUrl: apiUrlEl.value,
    });
    loadStats(apiUrlEl.value, domainEl.value, statsEl, apiBadgeEl);
  });

  clearCacheBtn.addEventListener("click", async () => {
    const all = await storageGet(null);
    const cacheKeys = Object.keys(all).filter(k => k.startsWith("cache_"));
    if (cacheKeys.length) await storageRemove(cacheKeys);
    clearCacheBtn.textContent = "Cache vidé !";
    setTimeout(() => { clearCacheBtn.textContent = "Vider le cache"; }, 1500);
  });
});

function setApiBadge(el, ok) {
  el.classList.remove("api-badge--ok", "api-badge--error", "api-badge--unknown");
  if (ok === true) {
    el.classList.add("api-badge--ok");
    el.textContent = "✓ API connectée";
  } else if (ok === false) {
    el.classList.add("api-badge--error");
    el.textContent = "✗ API indisponible";
  } else {
    el.classList.add("api-badge--unknown");
    el.textContent = "— Vérification…";
  }
}

async function loadStats(apiUrl, domainId, statsEl, apiBadgeEl) {
  setApiBadge(apiBadgeEl, null);
  try {
    const resp = await fetch(`${apiUrl}/api/domain/${encodeURIComponent(domainId)}/stats`);
    if (resp.ok) {
      const s = await resp.json();
      statsEl.textContent = `${s.count_new ?? "?"} classes, ${s.new_classes ?? 0} nouvelles, ${s.deprecated ?? 0} dépréciées`;
      setApiBadge(apiBadgeEl, true);
    } else if (resp.status === 404) {
      // API is reachable but the stats endpoint or domain is not found
      statsEl.textContent = "Statistiques indisponibles";
      setApiBadge(apiBadgeEl, true);
    } else {
      // Other HTTP error (5xx, etc.) — treat API as having issues
      statsEl.textContent = "Indisponible";
      setApiBadge(apiBadgeEl, false);
    }
  } catch (err) {
    // Network failure or fetch rejection (offline, CORS, etc.)
    statsEl.textContent = "Indisponible";
    console.error(err);
    setApiBadge(apiBadgeEl, false);
  }
}
