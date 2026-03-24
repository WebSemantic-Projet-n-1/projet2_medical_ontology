#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes pour les endpoints liés aux termes GO.

ENDPOINTS
---------
GET /api/term/{go_id}       — Infos d'un terme dans les deux versions
GET /api/term/{go_id}/diff  — Différences entre les deux versions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sparql_client import SparqlClient

router = APIRouter(prefix="/term", tags=["Termes GO"])
client = SparqlClient()


# ───
# MODÈLES DE RÉPONSE (Pydantic)
# ───

class TermEntry(BaseModel):
    """Métadonnées d'un terme GO dans une version donnée."""
    termURI:     str
    label:       str
    definition:  str
    isDeprecated: bool
    version:     str


class TermInfoResponse(BaseModel):
    """Réponse de GET /api/term/{go_id}"""
    go_id: str
    old:   TermEntry | None
    new:   TermEntry | None


class ChangeDetail(BaseModel):
    """Détail d'un changement entre deux versions."""
    field:            str
    old:              str | bool | None = None
    new:              str | bool | None = None
    added_parents:    list[str] | None = None
    removed_parents:  list[str] | None = None


class TermDiffResponse(BaseModel):
    """Réponse de GET /api/term/{go_id}/diff"""
    go_id:   str
    status:  str          # stable | modified | deprecated | new | not_found
    old:     TermEntry | None
    new:     TermEntry | None
    changes: list[ChangeDetail]


# ───
# ENDPOINTS
# ───

@router.get(
    "/{go_id}",
    response_model=TermInfoResponse,
    summary="Informations d'un terme GO",
    description=(
        "Retourne les métadonnées d'un terme GO dans ses deux versions "
        "(2025-10 et 2026-01). "
        "Si le terme est absent d'une version, le champ correspondant est `null`."
    ),
)
def get_term_info(go_id: str):
    """
    Paramètres
    ----------
    go_id : identifiant GO (ex: GO:0006281)
    """
    # Normalise le format : accepte "GO0006281", "go:0006281", "GO:0006281"
    go_id = _normalize_go_id(go_id)

    info = client.get_term_info(go_id)

    if info["old"] is None and info["new"] is None:
        raise HTTPException(
            status_code=404,
            detail=f"Terme {go_id} introuvable dans les deux versions."
        )

    return TermInfoResponse(go_id=go_id, **info)


@router.get(
    "/{go_id}/diff",
    response_model=TermDiffResponse,
    summary="Différences entre les deux versions d'un terme GO",
    description=(
        "Compare les deux versions d'un terme GO et retourne les différences. "
        "Le champ `status` indique : `stable`, `modified`, `deprecated`, `new`, ou `not_found`. "
        "Le champ `changes` liste chaque champ modifié avec son ancienne et nouvelle valeur."
    ),
)
def get_term_diff(go_id: str):
    """
    Paramètres
    ----------
    go_id : identifiant GO (ex: GO:0006281)
    """
    go_id = _normalize_go_id(go_id)

    diff = client.get_term_diff(go_id)

    if diff["status"] == "not_found":
        raise HTTPException(
            status_code=404,
            detail=f"Terme {go_id} introuvable dans les deux versions."
        )

    return TermDiffResponse(**diff)


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