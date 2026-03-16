#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes pour les endpoints de recherche de termes GO.

ENDPOINTS
---------
GET /api/search?q={query} — Recherche de termes par label ou définition
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from sparql_client import SparqlClient

router = APIRouter(prefix="/search", tags=["Recherche"])
client = SparqlClient()


# ───
# MODÈLES DE RÉPONSE (Pydantic)
# ───

class SearchResult(BaseModel):
    """Un résultat de recherche."""
    termID:     str
    label:      str
    definition: str
    version:    str


class SearchResponse(BaseModel):
    """Réponse de GET /api/search"""
    query:   str
    count:   int
    results: list[SearchResult]


# ───
# ENDPOINTS
# ───

@router.get(
    "",
    response_model=SearchResponse,
    summary="Recherche de termes GO",
    description=(
        "Recherche des termes GO par label ou définition (insensible à la casse). "
        "Retourne la version la plus récente (2026-01) de chaque terme trouvé. "
        "Exemples : `/api/search?q=repair`, `/api/search?q=nucleotide`."
    ),
)
def search(
    q: str = Query(
        ...,
        min_length=2,
        description="Mot-clé à rechercher dans les labels et définitions GO.",
        examples=["repair"],
    )
):
    """
    Paramètres
    ----------
    q : mot-clé de recherche (minimum 2 caractères)
    """
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Le paramètre 'q' ne peut pas être vide."
        )

    results = client.search(q.strip())

    return SearchResponse(
        query=q.strip(),
        count=len(results),
        results=[
            SearchResult(
                termID=r.get("termID", ""),
                label=r.get("label", ""),
                definition=r.get("definition", ""),
                version=r.get("version", ""),
            )
            for r in results
        ],
    )