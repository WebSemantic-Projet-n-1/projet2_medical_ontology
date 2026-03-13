/**
 * Popup — sauvegarde et chargement des options GO Evolution.
 * Compatible Firefox (browser.*) et Chrome (chrome.*).
 */

const API = globalThis.browser ?? globalThis.chrome;

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

  const stored = await API.storage.local.get(Object.keys(DEFAULTS));
  domainEl.value = stored.domain  || DEFAULTS.domain;
  apiUrlEl.value = stored.apiUrl  || DEFAULTS.apiUrl;

  loadStats(stored.apiUrl || DEFAULTS.apiUrl, domainEl.value, statsEl, apiBadgeEl);

  saveBtn.addEventListener("click", async () => {
    await API.storage.local.set({
      domain: domainEl.value,
      apiUrl: apiUrlEl.value,
    });
    loadStats(apiUrlEl.value, domainEl.value, statsEl, apiBadgeEl);
  });

  clearCacheBtn.addEventListener("click", async () => {
    const all = await API.storage.local.get(null);
    const cacheKeys = Object.keys(all).filter(k => k.startsWith("cache_"));
    if (cacheKeys.length) await API.storage.local.remove(cacheKeys);
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
  let resp;
  try {
    resp = await fetch(`${apiUrl}/api/domain/${domainId}/stats`);
  } catch {
    // Network error — API truly unreachable
    statsEl.textContent = "Indisponible";
    setApiBadge(apiBadgeEl, false);
    return;
  }

  if (resp.ok) {
    const s = await resp.json();
    statsEl.textContent = `${s.count_new || "?"} classes, ${s.new_classes || 0} nouvelles, ${s.deprecated || 0} dépréciées`;
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
}
