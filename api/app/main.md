# main.py — Documentation

## Rôle du fichier

`main.py` est le **point d'entrée** du service web. C'est lui qui crée
l'application FastAPI, configure le CORS, et branche les routes.
Il ne contient aucune logique métier — c'est uniquement de la configuration.

---

## Lancement

Depuis le dossier `api/app/` :

```bash
pip install uvicorn[standard]
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

| Option | Rôle |
|---|---|
| `main:app` | fichier `main.py`, variable `app` |
| `--reload` | redémarre automatiquement à chaque modification |
| `--host 0.0.0.0` | accessible depuis toutes les interfaces réseau |
| `--port 8000` | port d'écoute |

---

## Documentation automatique

FastAPI génère automatiquement deux interfaces de documentation :

| URL | Interface |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (interactif) |
| `http://localhost:8000/redoc` | ReDoc (lecture seule) |
| `http://localhost:8000/openapi.json` | Schéma OpenAPI brut |

---

## CORS

Le middleware CORS est activé pour permettre à l'extension de navigateur
(Partie 3) d'appeler l'API depuis une page web.
En développement, toutes les origines sont acceptées (`allow_origins=["*"]`).

---

## Routes enregistrées

| Préfixe | Fichier | Tag Swagger |
|---|---|---|
| `/api/term` | `routes/terms.py` | Termes GO |
| `/api/domain` | `routes/domain.py` | Domaines GO |
| `/api/search` | `routes/search.py` | Recherche |

---

## Health check

```
GET http://localhost:8000/
```

Retourne SI opérationnel :

```json
{
  "status": "ok",
  "service": "GO Evolution API",
  "version": "1.0.0",
  "docs": "/docs"
}
```