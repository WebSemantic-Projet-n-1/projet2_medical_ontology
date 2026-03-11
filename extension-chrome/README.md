# Extension Chrome – Évolution GO (Partie 3)

## Architecture (Manifest V3)

- **manifest.json** : métadonnées, permissions (storage, host permissions pour QuickGO/AmiGO/OLS), content_scripts, background (service_worker), popup.
- **background.js** : appels à l’API (service web), cache (IndexedDB ou storage), envoi des réponses au content script.
- **content.js** : détection des pages GO (URL pattern), extraction du GO ID, injection du badge (Stable / Modifié / Déprécié / Nouveau), popup détaillée au clic (définitions, hiérarchie, visualisation).
- **popup/** : popup de configuration (domaine, URL du service, cache on/off, stats).

## Chargement en développement

1. Ouvrir `chrome://extensions/`.
2. Activer « Mode développeur ».
3. « Charger l’extension non empaquetée » → sélectionner le dossier `extension-chrome/`.

## Pages cibles

- QuickGO : `https://www.ebi.ac.uk/QuickGO/term/GO:XXXXXXX`
- AmiGO 2 : `http://amigo.geneontology.org/amigo/term/GO:XXXXXXX`
- OLS : `https://www.ebi.ac.uk/ols/ontologies/go/terms/...`

Le content script doit détecter ces motifs et extraire l’identifiant GO pour appeler l’API puis afficher le badge et les détails.
