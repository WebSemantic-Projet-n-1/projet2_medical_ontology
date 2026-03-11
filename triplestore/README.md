# Triplestore – Partie 2

## Rôle

Stocker les deux versions de GO (ou le sous-domaine choisi) en RDF dans des **graphes nommés** pour permettre les requêtes SPARQL du service web.

- **Graphes suggérés** : `go:version/2025-10` et `go:version/2026-01` (ou selon les dates réelles des releases).
- **Modèle** : vocabulaire `evo:` (TermVersion, OntologyVersion, termID, version, label, definition, isDeprecated, parent, previousVersion, etc.) comme décrit dans l’énoncé.

## Options

### Apache Jena Fuseki

- Téléchargement : <https://jena.apache.org/download/>
- Démarrer : `fuseki-server` (ou script fourni). Créer un dataset (ex. `ds`) avec query/update.
- Endpoint de requête : `http://localhost:3030/ds/query` (GET/POST).
- Chargement des données : TDB2 ou upload via HTTP (voir doc Fuseki).

### GraphDB Free

- <https://graphdb.ontotext.com/>
- Créer un repository, configurer les graphes nommés, importer les RDF générés par les scripts d’extraction.

## Données

Les triplets RDF sont produits par le script d’extraction (Partie 2 : à placer dans `analyse/` ou un dossier dédié `service-web/etl/` selon votre choix). Ce dossier `triplestore/` contient la **configuration** et, si besoin, des exemples de requêtes SPARQL ou des fichiers de config Fuseki/GraphDB.

## Configuration du service web

Définir l’URL du endpoint SPARQL (variable d’environnement ou config), ex. :

- `SPARQL_ENDPOINT=http://localhost:3030/ds/query`

Sur Windows comme sur Linux, le service web lit cette variable pour interroger le triplestore.
