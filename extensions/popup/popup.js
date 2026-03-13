/**
 * Popup Firefox — sauvegarde et chargement des options GO Evolution.
 */

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

  const stored = await browser.storage.local.get(Object.keys(DEFAULTS));
  domainEl.value = stored.domain  || DEFAULTS.domain;
  apiUrlEl.value = stored.apiUrl  || DEFAULTS.apiUrl;

  loadStats(stored.apiUrl || DEFAULTS.apiUrl, domainEl.value, statsEl, apiBadgeEl);

  clearCacheBtn.addEventListener("click", async () => {
    const all = await browser.storage.local.get(null);
    const cacheKeys = Object.keys(all).filter(k => k.startsWith("cache_"));
    if (cacheKeys.length) await browser.storage.local.remove(cacheKeys);
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
    const resp = await fetch(`${apiUrl}/api/domain/${domainId}/stats`);
    if (!resp.ok) throw new Error(resp.status);
    const s = await resp.json();
    statsEl.textContent = `${s.count_new || "?"} classes, ${s.new_classes || 0} nouvelles, ${s.deprecated || 0} dépréciées`;
    setApiBadge(apiBadgeEl, true);
  } catch {
    statsEl.textContent = "Indisponible";
    setApiBadge(apiBadgeEl, false);
  }
}
