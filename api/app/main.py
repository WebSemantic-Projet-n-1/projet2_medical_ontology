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
from fastapi.responses import HTMLResponse
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
    """ Vérifie que l'API est fonctionnelle."""
    return {
        "status": "ok",
        "service": "GO Evolution API",
        "version": "1.0.0",
        "docs": "/docs",
    }

# def swagger_ui_html():

@app.get("/swagger", response_class=HTMLResponse, tags=["docs"])
def swagger_ui_html():
    """
    Swagger UI custom view rendering the OpenAPI YAML.
    """
    with open("openapi.yaml", "r", encoding="utf-8") as f:
        yaml_content = f.read()
    # Simple HTML rendering of the YAML (read-only, just for viewing)
    html = f"""
    <html>
    <head>
        <title>openapi.yaml (Swagger)</title>
        <style>
            body {{ font-family: monospace; background: #23272e; color: #eaeaea; }}
            pre  {{ background: #181c20; border-radius: 6px; padding: 20px; overflow-x: auto; font-size: 16px; line-height: 1.5; }}
        </style>
    </head>
    <body>
        <h2>openapi.yaml</h2>
        <pre>{yaml_content}</pre>
        <p><a href="/docs">[→ Documentation interactive /docs]</a></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)