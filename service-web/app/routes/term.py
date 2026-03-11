#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Routes API pour un terme GO.

STRUCTURE
---------
- GET /api/term/{go_id}
  Réponse : informations du terme dans les deux versions (label, definition, deprecated, parent, etc.).
  Source : sparql_client.get_term_info(go_id).

- GET /api/term/{go_id}/diff
  Réponse : JSON structuré des différences (definition_changed, hierarchy_changed, relations_added/removed, status: stable|modified|deprecated|new).
  Source : sparql_client.get_term_diff(go_id) puis construction du JSON côté route ou dans le client.
"""

# TODO: from fastapi import APIRouter, HTTPException
# TODO: from app.sparql_client import get_term_info, get_term_diff
# router = APIRouter()
# @router.get("/{go_id}") ...
# @router.get("/{go_id}/diff") ...
