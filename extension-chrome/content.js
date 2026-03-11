/**
 * Partie 3 - Content script : injection dans les pages GO (QuickGO, AmiGO, OLS).
 *
 * STRUCTURE
 * ---------
 * 1. Détection de la page : vérifier que l'URL correspond à un terme GO (pattern par site).
 * 2. Extraction du GO ID depuis l'URL (ex. GO:0006281) ou depuis le DOM (fallback).
 * 3. Envoyer un message au background : getTermDiff(goId).
 * 4. Réception de la réponse : status = stable | modified | deprecated | new.
 * 5. Injection d'un badge dans la page (position fixe ou près du titre du terme) avec le statut.
 * 6. Au clic sur le badge : afficher une popup détaillée (définitions côte à côte, ancien/nouveau parent, date, lien release notes).
 * 7. Pour "modified" : optionnellement afficher une visualisation simple des changements hiérarchiques (arbre comparatif).
 *
 * PATTERNS URL
 * ------------
 * QuickGO: .../QuickGO/term/GO:0006281
 * AmiGO:   .../amigo/term/GO:0006281
 * OLS:     .../ols/ontologies/go/terms/... (extraire GO ID du DOM ou URL)
 */

// TODO: const GO_ID_PATTERN = /GO:(\d{7})/;
// TODO: function getGoIdFromPage() { ... }
// TODO: function injectBadge(status, goId, details) { ... }
// TODO: function showDetailsPopup(diff) { ... }
// TODO: chrome.runtime.sendMessage({ action: "getTermDiff", goId }, response => { ... });
