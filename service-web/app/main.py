#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Point d'entrée FastAPI du service web d'analyse GO.

STRUCTURE
---------
1. Création de l'application FastAPI (titre, description, version).
2. Configuration CORS pour permettre les requêtes depuis l'extension (origine des pages GO).
3. Inclusion des routeurs : term, domain, search (sous /api/...).
4. (Optionnel) Redirection / -> /docs ou page d'accueil.
5. Démarrage avec uvicorn : uvicorn app.main:app --reload --host 0.0.0.0 --port 8000.

ENDPOINTS À MONTER
------------------
- /api/term/{go_id}         -> routes.term
- /api/term/{go_id}/diff    -> routes.term
- /api/domain/{domain_id}/stats -> routes.domain
- /api/search               -> routes.search
- /docs, /redoc             -> fournis par FastAPI (OpenAPI).
"""

# TODO: from fastapi import FastAPI
# TODO: from fastapi.middleware.cors import CORSMiddleware
# TODO: from app.routes import term, domain, search

# app = FastAPI(title="GO Evolution API", version="0.1.0", ...)
# app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
# app.include_router(term.router, prefix="/api/term", tags=["term"])
# app.include_router(domain.router, prefix="/api/domain", tags=["domain"])
# app.include_router(search.router, prefix="/api/search", tags=["search"])
