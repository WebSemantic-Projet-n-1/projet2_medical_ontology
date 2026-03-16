#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Point d'entrée du service web d'analyse GO (FastAPI).

UTILISATION
-----------
    uvicorn api.app.main:app --reload --host 0.0.0.0 --port 8000

DOCUMENTATION
-------------
    http://localhost:8000/docs        (Swagger UI)
    http://localhost:8000/redoc       (ReDoc)
    http://localhost:8000/openapi.json
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import domain, search, terms

# ───
# APPLICATION
# ───

app = FastAPI(
    title="GO Evolution API",
    description=(
        "Service web d'analyse de l'évolution de Gene Ontology (GO). "
        "Compare deux versions de GO (2025-10 et 2026-01) "
        "pour le domaine DNA repair (GO:0006281)."
    ),
    version="1.0.0",
    contact={
        "name": "INF6253 — Équipe",
        "email": "etiennegael.tajeuna@uqo.ca",
    },
    license_info={
        "name": "Université du Québec en Outaouais",
    },
)

# ───
# CORS — requis pour l'extension de navigateur (Partie 3)
# ───

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # À restreindre en production
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ───
# ROUTES
# ───

app.include_router(terms.router,  prefix="/api")
app.include_router(domain.router, prefix="/api")
app.include_router(search.router, prefix="/api")

# ───
# Test
# ───

@app.get("/", tags=["health"])
def root():
    """ ça Vérifie que l'API est fonctionnel."""
    return {
        "status": "ok",
        "service": "GO Evolution API",
        "version": "1.0.0",
        "docs": "/docs",
    }