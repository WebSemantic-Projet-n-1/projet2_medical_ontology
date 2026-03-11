#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Routes API pour la recherche de termes.

STRUCTURE
---------
- GET /api/search?q={query}
  Paramètre : q = chaîne de recherche (label ou définition).
  Réponse : liste de termes (go_id, label, definition, snippet) correspondant à la requête.
  Source : sparql_client.search(q).
"""

# TODO: from fastapi import APIRouter, Query
# TODO: from app.sparql_client import search
# router = APIRouter()
# @router.get("")  # query param q=...
