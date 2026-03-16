# API — GO Evolution

API REST (FastAPI) + Triplestore Apache Jena Fuseki pour interroger les deux versions de Gene Ontology.

## Structure

```
api/
├── app/               # Application FastAPI
│   └── routes/        # Endpoints REST
├── triplestore/
│   └── config/
│       ├── fuseki.ttl     # Configuration du dataset TDB2
│       ├── load-data.sh   # Chargement des OWL (Linux/Docker)
│       └── load-data.ps1  # Chargement des OWL (Windows)
├── docker-compose.yml
├── .env               # Variables locales (non versionné)
└── .env.example       # Template à copier
```

## Prérequis

- Docker 24+ et Docker Compose v2
- Fichiers OWL dans `../data/` :
  - `gene-ontology-10-25/data/ontology/go.owl` (version octobre 2025)
  - `gene-ontology-01-26/data/ontology/go.owl` (version janvier 2026)

## Lancer le triplestore

```bash
# 1. Copier et ajuster les variables d'environnement
cp .env.example .env

# 2. Démarrer Fuseki + chargement automatique des données
docker compose up -d

# 3. Vérifier que Fuseki est prêt
docker compose logs -f fuseki
```

| URL | Description |
|-----|-------------|
| <http://localhost:3030> | Interface admin Fuseki |
| <http://localhost:3030/ds/query> | Endpoint SPARQL |

Le chargement des données OWL (premier démarrage uniquement) est automatique via le service `fuseki-loader`. Les données sont stockées dans le volume Docker `go-fuseki-data` et survivent aux redémarrages.

## Commandes utiles

```bash
# Voir les logs du chargeur
docker compose logs fuseki-loader

# Arrêter (données conservées)
docker compose down

# Repartir de zéro (supprime le volume TDB2)
docker compose down -v
```

## Variables d'environnement (`.env`)

| Variable | Défaut | Description |
|----------|--------|-------------|
| `ADMIN_PASSWORD` | `admin` | Mot de passe interface admin Fuseki |
| `JVM_ARGS` | `-Xmx2g` | Mémoire JVM allouée à Fuseki |
| `FUSEKI_URL` | `http://fuseki:3030` | URL interne Fuseki (entre conteneurs) |
| `FUSEKI_DATASET` | `ds` | Nom du dataset SPARQL |
| `SPARQL_ENDPOINT` | `http://localhost:3030/ds/query` | Endpoint utilisé par l'API |

# Serveur web

| URL | Interface |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (interactif) |
| `http://localhost:8000/redoc` | ReDoc (lecture seule) |
| `http://localhost:8000/openapi.json` | Schéma OpenAPI brut |