# Extension Firefox – Évolution GO (Partie 3, optionnel)

## Manifest V2

Firefox supporte les WebExtensions avec Manifest V2 (et V3 en cours). Ce dossier peut réutiliser la même logique que `extension-chrome/` avec les différences suivantes :

- **manifest.json** : `manifest_version: 2`, `background.scripts: ["background.js"]` au lieu de `service_worker`.
- **background.js** : pas de service worker ; script persistant (même API `chrome.runtime.onMessage` / `browser.runtime`).
- **host_permissions** : en V2, utiliser `permissions` avec les URLs.

Pour garder le projet KISS, vous pouvez :
1. Développer d’abord l’extension Chrome, puis adapter le manifest et le background pour Firefox.
2. Ou maintenir un seul dossier et générer deux manifests à partir d’un template si nécessaire.

Structure suggérée : même que `extension-chrome/` (content.js, content.css, popup/, background.js) avec un `manifest.json` Firefox (V2).
