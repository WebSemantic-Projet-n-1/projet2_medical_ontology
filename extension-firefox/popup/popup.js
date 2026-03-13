/**
 * Popup Firefox — sauvegarde et chargement des options GO Evolution.
 */

const DEFAULTS = {
  domain: "0006281",
  apiUrl: "http://localhost:8000",
  cacheEnabled: true,
};

document.addEventListener("DOMContentLoaded", async () => {
  const domainEl = document.getElementById("domain");
  const apiUrlEl = document.getElementById("apiUrl");
  const cacheEl = document.getElementById("cacheEnabled");
  const saveBtn = document.getElementById("save");
  const statsEl = document.getElementById("stats");

  const stored = await browser.storage.local.get(Object.keys(DEFAULTS));
  domainEl.value = stored.domain || DEFAULTS.domain;
  apiUrlEl.value = stored.apiUrl || DEFAULTS.apiUrl;
  cacheEl.checked = stored.cacheEnabled ?? DEFAULTS.cacheEnabled;

  loadStats(stored.apiUrl || DEFAULTS.apiUrl, domainEl.value, statsEl);

  saveBtn.addEventListener("click", async () => {
    await browser.storage.local.set({
      domain: domainEl.value,
      apiUrl: apiUrlEl.value,
      cacheEnabled: cacheEl.checked,
    });
    saveBtn.textContent = "Enregistré !";
    setTimeout(() => { saveBtn.textContent = "Enregistrer"; }, 1200);

    loadStats(apiUrlEl.value, domainEl.value, statsEl);
  });
});

async function loadStats(apiUrl, domainId, el) {
  try {
    const resp = await fetch(`${apiUrl}/api/domain/${domainId}/stats`);
    if (!resp.ok) throw new Error(resp.status);
    const s = resp.json ? await resp.json() : {};
    el.textContent = `${s.count_new || "?"} classes, ${s.new_classes || 0} nouvelles, ${s.deprecated || 0} dépréciées`;
  } catch {
    el.textContent = "API indisponible";
  }
}
