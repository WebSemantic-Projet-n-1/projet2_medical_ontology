/**
 * Partie 3 - Background script (service worker Manifest V3).
 *
 * STRUCTURE
 * ---------
 * 1. Écouter les messages du content script (demande d'infos ou diff pour un go_id).
 * 2. Vérifier le cache local (IndexedDB ou chrome.storage) ; si présent et valide, renvoyer le cache.
 * 3. Sinon : appeler l'API (URL configurable, ex. GET /api/term/{go_id}/diff).
 * 4. Mettre en cache la réponse (avec TTL ou version).
 * 5. Renvoyer la réponse au content script.
 *
 * MESSAGES ATTENDUS
 * -----------------
 * - { action: "getTermDiff", goId: "GO:0006281" } -> réponse diff ou erreur.
 * - (Optionnel) { action: "getTermInfo", goId: "..." }.
 * - (Optionnel) { action: "getDomainStats", domainId: "0006281" }.
 *
 * CONFIG
 * ------
 * Lire depuis chrome.storage.sync ou local : apiBaseUrl, cacheEnabled, domainId.
 */

// TODO: ouvrir IndexedDB ou utiliser chrome.storage pour le cache
// TODO: chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => { ... })
// TODO: fonction fetchTermDiff(goId) -> appel fetch(apiBaseUrl + "/api/term/" + goId + "/diff")
// TODO: fonction getCached(key), setCached(key, value, ttl)
