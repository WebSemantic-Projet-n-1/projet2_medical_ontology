# Partie 2 : Service web d’analyse GO

## Device : CUDA en priorité, repli CPU

Pour tout code utilisant PyTorch (ex. embeddings) dans l’API : `from util.device import get_device`. Lancer depuis la racine du projet avec `PYTHONPATH=.` si besoin pour que le module `util` soit importable (ex. `PYTHONPATH=. uvicorn app.main:app --reload` depuis `service-web/`).

## Rôle

- API REST (FastAPI) qui interroge le triplestore (SPARQL) et expose :
  - `GET /api/term/{go_id}` : infos d’un terme dans les deux versions
  - `GET /api/term/{go_id}/diff` : différences entre versions (JSON)
  - `GET /api/domain/{domain_id}/stats` : statistiques d’évolution du domaine
  - `GET /api/search?q={query}` : recherche par label ou définition
- Documentation OpenAPI : `openapi.yaml` et Swagger UI à `/docs`.

## Structure

- `app/main.py` : point d’entrée FastAPI, montage des routes, CORS.
- `app/sparql_client.py` : client SPARQL vers le triplestore (Fuseki/GraphDB).
- `app/routes/` : modules par ressource (term, domain, search).
- `openapi.yaml` : schéma OpenAPI (peut être généré par FastAPI ; ce fichier sert de référence).

## Lancer le service

Avec le venv activé et le triplestore démarré. Depuis la racine du projet (pour `util` si besoin) ou depuis `service-web/` :

```bash
cd service-web
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Depuis la racine avec util importable : cd service-web && PYTHONPATH=.. uvicorn app.main:app --reload ...
```

Documentation interactive : http://localhost:8000/docs

## Configuration

- URL du triplestore : variable d’environnement ou fichier de config (ex. `SPARQL_ENDPOINT=http://localhost:3030/ds/query`).
