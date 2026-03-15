#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Client SPARQL pour interroger le triplestore (Jena Fuseki) > DOcker.

STRUCTURE
---------
1. Classe SparqlClient avec l'URL du endpoint (configurable via .env).
2. Méthode query(sparql_str) -> liste de bindings.
3. Méthodes dédiées par usage :
   - get_term_info(go_id)       : infos d'un terme pour les deux versions.
   - get_term_diff(go_id)       : différences entre les deux versions.
   - get_domain_stats(domain_id): agrégats pour le domaine DNA repair.
   - search(q)                  : recherche par label ou définition.
4. Gestion des erreurs (timeout, 4xx/5xx) et logs.

NAMESPACES / GRAPHES
--------------------
- http://example.org/go/version/2025-10
- http://example.org/go/version/2026-01
- Préfixes : go:, evo:, rdfs:, owl:, xsd:

DÉPENDANCES (Importante !)
-----------
    pip install sparqlwrapper python-dotenv
"""

import logging
import os

from dotenv import load_dotenv
from SPARQLWrapper import JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

load_dotenv()

# ───
# CONFIG
# ───

ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://localhost:3030/ds/sparql")

# Lien important pour différencier sans besoin d'exister réellement
GRAPH_OLD = "http://example.org/go/version/2025-10"
GRAPH_NEW = "http://example.org/go/version/2026-01"

# Préfixes SPARQL
PREFIXES = """
PREFIX evo:  <http://example.org/evolution/>
PREFIX go:   <http://purl.obolibrary.org/obo/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
"""

# ───
# LOGGING
# ───

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


# ───
# CLIENT SPARQL
# ───

class SparqlClient:
    """
    Client SPARQL pour interroger Apache Jena Fuseki.
    Toutes les méthodes retournent des dicts/listes Python purs,
    sans objet SPARQLWrapper — facile à sérialiser en JSON pour l'API.
    """

    def __init__(self, endpoint: str = ENDPOINT):
        self.endpoint = endpoint
        self._sparql  = SPARQLWrapper(endpoint)
        self._sparql.setReturnFormat(JSON)
        log.info(f"SparqlClient initialisé sur {endpoint}")

    # ── Méthode de base ──

    def query(self, sparql_str: str) -> list[dict]:
        """
        Exécute une requête SPARQL SELECT et retourne les résultats
        sous forme de liste de dicts {variable: valeur}.

        Paramètres
        ----------
        sparql_str : requête SPARQL complète (avec préfixes si nécessaire)

        Retourne
        --------
        Liste de dicts, une entrée par ligne de résultat.
        Retourne [] en cas d'erreur.
        """
        try:
            self._sparql.setQuery(sparql_str)
            results = self._sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            # Aplatit les bindings : {"x": {"type": "literal", "value": "abc"}} -> {"x": "abc"}
            return [
                {k: v["value"] for k, v in row.items()}
                for row in bindings
            ]
        except SPARQLWrapperException as e:
            log.error(f"Erreur SPARQL : {e}")
            return []
        except Exception as e:
            log.error(f"Erreur inattendue : {e}")
            return []

    # ── GET /api/term/{go_id} ──

    def get_term_info(self, go_id: str) -> dict:
        """
        Retourne les informations d'un terme GO dans ses deux versions.

        Paramètres
        ----------
        go_id : identifiant GO (ex: "GO:0006281")

        Retourne
        --------
        Dict avec les clés "old" et "new", chacune contenant
        label, definition, isDeprecated, parents.
        """
        sparql = PREFIXES + f"""
        SELECT ?termURI ?label ?definition ?isDeprecated ?version
        WHERE {{
            GRAPH ?g {{
                ?termURI evo:termID "{go_id}" ;
                         evo:label ?label ;
                         evo:definition ?definition ;
                         evo:isDeprecated ?isDeprecated ;
                         evo:belongsToVersion ?version .
            }}
        }}
        """
        rows = self.query(sparql)

        result = {"old": None, "new": None}
        for row in rows:
            version = row.get("version", "")
            entry = {
                "termURI":     row.get("termURI"),
                "label":       row.get("label"),
                "definition":  row.get("definition"),
                "isDeprecated": row.get("isDeprecated") == "true",
                "version":     version,
            }
            if "2025-10" in version:
                result["old"] = entry
            elif "2026-01" in version:
                result["new"] = entry

        return result

    # ── GET /api/term/{go_id}/diff ────────────────────────────

    def get_term_diff(self, go_id: str) -> dict:
        """
        Retourne les différences entre les deux versions d'un terme GO.

        Paramètres
        ----------
        go_id : identifiant GO (ex: "GO:0006281")

        Retourne
        --------
        Dict avec les champs modifiés entre les deux versions :
        label, definition, isDeprecated, parents.
        Un champ "status" indique : stable | modified | deprecated | new.
        """
        info = self.get_term_info(go_id)
        old  = info.get("old")
        new  = info.get("new")

        # Terme nouveau (absent de l'ancienne version)
        if old is None and new is not None:
            return {"go_id": go_id, "status": "new", "old": None, "new": new, "changes": []}

        # Terme disparu (absent de la nouvelle version)
        if new is None and old is not None:
            return {"go_id": go_id, "status": "deprecated", "old": old, "new": None, "changes": []}

        # Terme absent des deux versions
        if old is None and new is None:
            return {"go_id": go_id, "status": "not_found", "old": None, "new": None, "changes": []}

        # Comparaison champ par champ
        changes = []

        if old["label"] != new["label"]:
            changes.append({
                "field": "label",
                "old":   old["label"],
                "new":   new["label"],
            })

        if old["definition"] != new["definition"]:
            changes.append({
                "field": "definition",
                "old":   old["definition"],
                "new":   new["definition"],
            })

        if old["isDeprecated"] != new["isDeprecated"]:
            changes.append({
                "field": "isDeprecated",
                "old":   old["isDeprecated"],
                "new":   new["isDeprecated"],
            })

        # Parents
        old_parents = self._get_parents(go_id, GRAPH_OLD)
        new_parents = self._get_parents(go_id, GRAPH_NEW)

        added_parents   = list(set(new_parents) - set(old_parents))
        removed_parents = list(set(old_parents) - set(new_parents))

        if added_parents or removed_parents:
            changes.append({
                "field":           "parents",
                "added_parents":   added_parents,
                "removed_parents": removed_parents,
            })

        status = "modified" if changes else "stable"
        if new.get("isDeprecated"):
            status = "deprecated"

        return {
            "go_id":   go_id,
            "status":  status,
            "old":     old,
            "new":     new,
            "changes": changes,
        }

    def _get_parents(self, go_id: str, graph_uri: str) -> list[str]:
        """Retourne les termID des parents directs d'un terme dans un graphe donné."""
        sparql = PREFIXES + f"""
        SELECT ?parentID
        WHERE {{
            GRAPH <{graph_uri}> {{
                ?term evo:termID "{go_id}" ;
                      evo:hasParent ?parent .
                ?parent evo:termID ?parentID .
            }}
        }}
        """
        rows = self.query(sparql)
        return [row["parentID"] for row in rows]

    # ── GET /api/domain/{domain_id}/stats ─────────────────────

    def get_domain_stats(self, domain_id: str) -> dict:
        """
        Retourne les statistiques d'évolution pour un domaine GO.

        Paramètres
        ----------
        domain_id : identifiant GO de la racine du domaine (ex: "GO:0006281")

        Retourne
        --------
        Dict avec : total_old, total_new, new_terms, deprecated_terms,
                    modified_terms, stable_terms.
        """
        # Nombre de termes par version
        total_old = self._count_terms(GRAPH_OLD)
        total_new = self._count_terms(GRAPH_NEW)

        # Termes présents dans chaque version
        terms_old = set(self._get_all_term_ids(GRAPH_OLD))
        terms_new = set(self._get_all_term_ids(GRAPH_NEW))

        new_terms        = list(terms_new - terms_old)
        disappeared_terms = list(terms_old - terms_new)
        common_terms     = terms_old & terms_new

        # Termes modifiés parmi les communs
        modified = []
        stable   = []
        for go_id in common_terms:
            diff = self.get_term_diff(go_id)
            if diff["status"] == "modified":
                modified.append(go_id)
            else:
                stable.append(go_id)

        return {
            "domain_id":         domain_id,
            "total_old":         total_old,
            "total_new":         total_new,
            "new_terms":         new_terms,
            "new_terms_count":   len(new_terms),
            "deprecated_terms":  disappeared_terms,
            "deprecated_count":  len(disappeared_terms),
            "modified_terms":    modified,
            "modified_count":    len(modified),
            "stable_terms":      stable,
            "stable_count":      len(stable),
        }

    def _count_terms(self, graph_uri: str) -> int:
        """Compte le nombre de TermVersion dans un graphe nommé."""
        sparql = PREFIXES + f"""
        SELECT (COUNT(?t) AS ?count)
        WHERE {{
            GRAPH <{graph_uri}> {{
                ?t a evo:TermVersion .
            }}
        }}
        """
        rows = self.query(sparql)
        if rows:
            return int(rows[0].get("count", 0))
        return 0

    def _get_all_term_ids(self, graph_uri: str) -> list[str]:
        """Retourne tous les termID présents dans un graphe nommé."""
        sparql = PREFIXES + f"""
        SELECT ?termID
        WHERE {{
            GRAPH <{graph_uri}> {{
                ?t a evo:TermVersion ;
                   evo:termID ?termID .
            }}
        }}
        """
        rows = self.query(sparql)
        return [row["termID"] for row in rows]

    # ── GET /api/search?q={query} ─────────────────────────────

    def search(self, q: str) -> list[dict]:
        """
        Recherche des termes GO par label ou définition.
        Utilise FILTER regex (insensible à la casse).

        Paramètres
        ----------
        q : chaîne de recherche (ex: "repair", "nucleotide")

        Retourne
        --------
        Liste de dicts avec termID, label, definition, version.
        Les doublons (même terme dans les deux versions) sont dédupliqués
        — on retourne la version la plus récente (2026-01).
        """
        # Échapper les caractères spéciaux regex
        q_escaped = q.replace("\\", "\\\\").replace('"', '\\"')

        sparql = PREFIXES + f"""
        SELECT DISTINCT ?termID ?label ?definition ?version
        WHERE {{
            GRAPH ?g {{
                ?t a evo:TermVersion ;
                   evo:termID ?termID ;
                   evo:label ?label ;
                   evo:definition ?definition ;
                   evo:belongsToVersion ?version .
                FILTER (
                    regex(str(?label), "{q_escaped}", "i") ||
                    regex(str(?definition), "{q_escaped}", "i")
                )
            }}
        }}
        ORDER BY ?termID ?version
        """
        rows = self.query(sparql)

        # Déduplique : garde la version la plus récente par termID
        seen    = {}
        for row in rows:
            tid = row.get("termID")
            if tid not in seen or "2026" in row.get("version", ""):
                seen[tid] = row

        return list(seen.values())


# ───
# USAGE DIRECT (test rapide)
# ───

if __name__ == "__main__":
    client = SparqlClient()

    print("\n=== Test get_term_info(GO:0006281) ===")
    info = client.get_term_info("GO:0006281")
    print(info)

    print("\n=== Test get_term_diff(GO:0006281) ===")
    diff = client.get_term_diff("GO:0006281")
    print(diff)

    print("\n=== Test get_domain_stats(GO:0006281) ===")
    stats = client.get_domain_stats("GO:0006281")
    print(stats)

    print("\n=== Test search('repair') ===")
    results = client.search("repair")
    for r in results:
        print(f"  {r['termID']} — {r['label']}")