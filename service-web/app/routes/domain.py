#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Routes API pour les statistiques d'un domaine.

STRUCTURE
---------
- GET /api/domain/{domain_id}/stats
  Paramètre : domain_id = GO ID racine du domaine (ex. 0006281 pour DNA repair).
  Réponse : statistiques d'évolution (nb classes v1, v2, new, deprecated, hierarchy_changed, etc.).
  Source : sparql_client.get_domain_stats(domain_id).
"""

# TODO: from fastapi import APIRouter, HTTPException
# TODO: from app.sparql_client import get_domain_stats
# router = APIRouter()
# @router.get("/{domain_id}/stats") ...
