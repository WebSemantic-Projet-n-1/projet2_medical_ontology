#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes pour les endpoints liés aux statistiques d'un domaine GO.

ENDPOINTS
---------
GET /api/domain/{domain_id}/stats — Statistiques d'évolution pour un domaine
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sparql_client import SparqlClient

router = APIRouter(prefix="/domain", tags=["Domaines GO"])
client = SparqlClient()


# ───
# MODÈLES DE RÉPONSE (Pydantic)
# ───

class DomainStatsResponse(BaseModel):
    """Réponse de GET /api/domain/{domain_id}/stats"""
    domain_id:        str
    total_old:        int
    total_new:        int
    new_terms:        list[str]
    new_terms_count:  int
    deprecated_terms: list[str]
    deprecated_count: int
    modified_terms:   list[str]
    modified_count:   int
    stable_terms:     list[str]
    stable_count:     int


# ───
# ENDPOINTS
# ───

@router.get(
    "/{domain_id}/stats",
    response_model=DomainStatsResponse,
    summary="Statistiques d'évolution d'un domaine GO",
    description=(
        "Retourne les statistiques d'évolution pour un domaine GO entre "
        "les versions 2025-10 et 2026-01. "
        "Inclut le nombre de termes nouveaux, dépréciés, modifiés et stables. "
        "Exemple : `/api/domain/GO:0006281/stats` pour le domaine DNA repair."
    ),
)
def get_domain_stats(domain_id: str):
    """
    Paramètres
    ----------
    domain_id : identifiant GO de la racine du domaine (ex: GO:0006281)
    """
    domain_id = _normalize_go_id(domain_id)

    stats = client.get_domain_stats(domain_id)

    if stats["total_old"] == 0 and stats["total_new"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Domaine {domain_id} introuvable dans le triplestore."
        )

    return DomainStatsResponse(**stats)


# ───
# UTILITAIRE
# ───

def _normalize_go_id(go_id: str) -> str:
    """
    Normalise un identifiant GO en format standard "GO:XXXXXXX".
    Accepte : "GO0006281", "go:0006281", "GO:0006281", "0006281"
    """
    go_id = go_id.strip().upper()
    if go_id.startswith("GO:"):
        return go_id
    if go_id.startswith("GO"):
        return f"GO:{go_id[2:]}"
    return f"GO:{go_id}"