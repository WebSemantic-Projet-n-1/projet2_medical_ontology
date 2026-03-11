#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Client SPARQL pour interroger le triplestore (Jena Fuseki / GraphDB).

STRUCTURE
---------
1. Classe ou module avec l'URL du endpoint (configurable : env ou paramètre).
2. Méthode query( sparql_str ) -> résultats (JSON ou liste de bindings).
3. Méthodes dédiées par usage :
   - get_term_info(go_id) : infos d'un terme pour les deux versions (graphes nommés).
   - get_term_diff(go_id) : triplets nécessaires pour construire le diff.
   - get_domain_stats(domain_id) : agrégats pour le domaine.
   - search(query) : recherche par label/définition (FILTER regex ou full-text si dispo).
4. Gestion des erreurs (timeout, 4xx/5xx) et logs.

NAMESPACES / GRAPhes
--------------------
- go:version/2025-10 et go:version/2026-01 (ou selon vos dates).
- Préfixes : go:, evo:, rdfs:, owl:, xsd:.

DEVICE (CUDA / CPU)
-------------------
Si des appels à des modèles (embeddings, etc.) sont faits côté service : from util.device import get_device.
Priorité CUDA, repli CPU.
"""

# TODO: from SPARQLWrapper import SPARQLWrapper
# TODO: import os
# TODO: ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://localhost:3030/ds/query")
# TODO: def query(sparql: str) -> ...
# TODO: def get_term_info(go_id: str) -> dict
# TODO: def get_term_diff(go_id: str) -> dict
# TODO: def get_domain_stats(domain_id: str) -> dict
# TODO: def search(q: str) -> list
