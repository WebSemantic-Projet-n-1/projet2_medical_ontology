#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Matérialise les liens evo:previousVersion dans Fuseki, valide le résultat,
et sauvegarde des métriques utiles pour le rapport du projet.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

PREFIXES = """
PREFIX evo:  <http://example.org/evolution/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

GRAPH_OLD = "http://example.org/go/version/2025-10"
GRAPH_NEW = "http://example.org/go/version/2026-01"
GRAPH_INFERRED = "http://example.org/go/inferred"


def env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


FUSEKI_URL = env("FUSEKI_URL", "http://fuseki:3030")
FUSEKI_DATASET = env("FUSEKI_DATASET", "ds")
ADMIN_PASSWORD = env("ADMIN_PASSWORD", "admin")
QUERY_FILE = Path(env("QUERY_FILE", "/app/triplestore/sparql/materialize_previous_version.ru"))
MARKER_DIR = Path(env("MARKER_DIR", "/marker"))
OUTPUT_DIR = Path(env("METRICS_OUTPUT_DIR", "/output"))
MARKER = MARKER_DIR / ".inference-done"

UPDATE_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/update"
QUERY_URL = f"{FUSEKI_URL}/{FUSEKI_DATASET}/query"


def log(message: str) -> None:
    print(f"[inference] {message}", flush=True)


def select_rows(sparql: str) -> list[dict[str, str]]:
    response = requests.get(
        QUERY_URL,
        params={"query": sparql},
        headers={"Accept": "application/sparql-results+json"},
        auth=("admin", ADMIN_PASSWORD),
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    bindings = payload.get("results", {}).get("bindings", [])
    return [{key: value["value"] for key, value in row.items()} for row in bindings]


def post_update(sparql_update: str) -> None:
    response = requests.post(
        UPDATE_URL,
        data=sparql_update.encode("utf-8"),
        headers={"Content-Type": "application/sparql-update"},
        auth=("admin", ADMIN_PASSWORD),
        timeout=60,
    )
    response.raise_for_status()


def to_bool(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def load_terms(graph_uri: str) -> dict[str, dict[str, Any]]:
    term_rows = select_rows(
        PREFIXES
        + f"""
SELECT ?term ?termID ?label ?definition ?isDeprecated
WHERE {{
    GRAPH <{graph_uri}> {{
        ?term a evo:TermVersion ;
              evo:termID ?termID ;
              evo:isDeprecated ?isDeprecated .
        OPTIONAL {{ ?term evo:label ?label . }}
        OPTIONAL {{ ?term evo:definition ?definition . }}
    }}
}}
"""
    )

    terms: dict[str, dict[str, Any]] = {}
    for row in term_rows:
        term_id = row["termID"]
        terms[term_id] = {
            "uri": row["term"],
            "label": row.get("label", ""),
            "definition": row.get("definition", ""),
            "isDeprecated": to_bool(row.get("isDeprecated")),
            "parents": set(),
        }

    parent_rows = select_rows(
        PREFIXES
        + f"""
SELECT ?termID ?parent ?parentID
WHERE {{
    GRAPH <{graph_uri}> {{
        ?term a evo:TermVersion ;
              evo:termID ?termID ;
              evo:hasParent ?parent .
        OPTIONAL {{ ?parent evo:termID ?parentID . }}
    }}
}}
"""
    )

    for row in parent_rows:
        term_id = row["termID"]
        if term_id not in terms:
            continue
        parent_ref = row.get("parentID") or row["parent"]
        terms[term_id]["parents"].add(parent_ref)

    return terms


def load_inferred_links() -> list[dict[str, str]]:
    return select_rows(
        PREFIXES
        + f"""
SELECT ?newTerm ?newTermID ?oldTerm ?oldTermID
WHERE {{
    GRAPH <{GRAPH_INFERRED}> {{
        ?newTerm evo:previousVersion ?oldTerm .
    }}
    GRAPH <{GRAPH_NEW}> {{
        ?newTerm evo:termID ?newTermID .
    }}
    GRAPH <{GRAPH_OLD}> {{
        ?oldTerm evo:termID ?oldTermID .
    }}
}}
ORDER BY ?newTermID
"""
    )


def compute_metrics(
    terms_old: dict[str, dict[str, Any]],
    terms_new: dict[str, dict[str, Any]],
    links: list[dict[str, str]],
) -> dict[str, Any]:
    old_ids = set(terms_old)
    new_ids = set(terms_new)
    common_ids = old_ids & new_ids
    new_only_ids = new_ids - old_ids
    disappeared_ids = old_ids - new_ids

    hierarchy_changed = sorted(
        term_id
        for term_id in common_ids
        if terms_old[term_id]["parents"] != terms_new[term_id]["parents"]
    )
    labels_changed = sorted(
        term_id
        for term_id in common_ids
        if terms_old[term_id]["label"] != terms_new[term_id]["label"]
    )
    definitions_changed = sorted(
        term_id
        for term_id in common_ids
        if terms_old[term_id]["definition"] != terms_new[term_id]["definition"]
    )
    deprecation_changed = sorted(
        term_id
        for term_id in common_ids
        if terms_old[term_id]["isDeprecated"] != terms_new[term_id]["isDeprecated"]
    )

    modified_ids = sorted(
        {
            *hierarchy_changed,
            *labels_changed,
            *definitions_changed,
            *deprecation_changed,
        }
    )
    stable_ids = sorted(common_ids - set(modified_ids))

    previous_by_new: dict[str, set[str]] = {}
    mismatched_term_ids: list[dict[str, str]] = []
    self_uri_links: list[dict[str, str]] = []
    invalid_sources: list[dict[str, str]] = []
    invalid_targets: list[dict[str, str]] = []
    unexpected_linked_terms: list[dict[str, str]] = []

    for row in links:
        new_term_id = row["newTermID"]
        old_term_id = row["oldTermID"]
        previous_by_new.setdefault(new_term_id, set()).add(old_term_id)

        if new_term_id != old_term_id:
            mismatched_term_ids.append(row)
        if row["newTerm"] == row["oldTerm"]:
            self_uri_links.append(row)

        expected_new_uri = terms_new.get(new_term_id, {}).get("uri")
        expected_old_uri = terms_old.get(old_term_id, {}).get("uri")
        if expected_new_uri != row["newTerm"]:
            invalid_sources.append(row)
        if expected_old_uri != row["oldTerm"]:
            invalid_targets.append(row)
        if new_term_id not in common_ids:
            unexpected_linked_terms.append(row)

    duplicate_previous = sorted(
        term_id for term_id, previous_ids in previous_by_new.items() if len(previous_ids) > 1
    )
    missing_previous = sorted(term_id for term_id in common_ids if term_id not in previous_by_new)

    deprecated_old = sorted(term_id for term_id, data in terms_old.items() if data["isDeprecated"])
    deprecated_new = sorted(term_id for term_id, data in terms_new.items() if data["isDeprecated"])

    validations = {
        "common_terms_have_previous_version": {
            "ok": not missing_previous,
            "count": len(missing_previous),
            "examples": missing_previous[:10],
        },
        "each_new_term_has_at_most_one_previous_version": {
            "ok": not duplicate_previous,
            "count": len(duplicate_previous),
            "examples": duplicate_previous[:10],
        },
        "inferred_links_match_same_term_id": {
            "ok": not mismatched_term_ids,
            "count": len(mismatched_term_ids),
            "examples": mismatched_term_ids[:5],
        },
        "inferred_link_sources_exist_in_new_graph": {
            "ok": not invalid_sources,
            "count": len(invalid_sources),
            "examples": invalid_sources[:5],
        },
        "inferred_link_targets_exist_in_old_graph": {
            "ok": not invalid_targets,
            "count": len(invalid_targets),
            "examples": invalid_targets[:5],
        },
        "no_self_uri_links": {
            "ok": not self_uri_links,
            "count": len(self_uri_links),
            "examples": self_uri_links[:5],
        },
        "no_links_for_new_only_terms": {
            "ok": not unexpected_linked_terms,
            "count": len(unexpected_linked_terms),
            "examples": unexpected_linked_terms[:5],
        },
    }

    validation_passed = all(check["ok"] for check in validations.values())

    return {
        "validation_passed": validation_passed,
        "metrics": {
            "required_project_metrics": {
                "classes_old_version_count": len(terms_old),
                "classes_new_version_count": len(terms_new),
                "new_classes_count": len(new_only_ids),
                "deprecated_classes_old_count": len(deprecated_old),
                "deprecated_classes_new_count": len(deprecated_new),
                "hierarchy_changed_classes_count": len(hierarchy_changed),
            },
            "additional_metrics": {
                "common_classes_count": len(common_ids),
                "disappeared_classes_count": len(disappeared_ids),
                "inferred_previous_version_links_count": len(links),
                "inference_coverage_ratio": round(
                    len(links) / len(common_ids), 4
                ) if common_ids else 1.0,
                "labels_changed_count": len(labels_changed),
                "definitions_changed_count": len(definitions_changed),
                "deprecation_status_changed_count": len(deprecation_changed),
                "modified_classes_count": len(modified_ids),
                "stable_classes_count": len(stable_ids),
            },
        },
        "details": {
            "new_classes": sorted(new_only_ids),
            "disappeared_classes": sorted(disappeared_ids),
            "deprecated_classes_old": deprecated_old,
            "deprecated_classes_new": deprecated_new,
            "hierarchy_changed_classes": hierarchy_changed,
            "labels_changed_classes": labels_changed,
            "definitions_changed_classes": definitions_changed,
            "deprecation_changed_classes": deprecation_changed,
            "modified_classes": modified_ids,
            "stable_classes": stable_ids,
            "missing_previous_version_links": missing_previous,
            "duplicate_previous_version_links": duplicate_previous,
        },
        "validations": validations,
    }


def write_metrics(payload: dict[str, Any]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "inference_validation_metrics.json"
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return output_path


def main() -> int:
    started_at = time.perf_counter()

    if MARKER.exists():
        log(f"Inférences déjà matérialisées ({MARKER} trouvé). Abandon.")
        return 0

    if not QUERY_FILE.exists():
        log(f"ERREUR : fichier SPARQL introuvable : {QUERY_FILE}")
        return 1

    sparql_update = QUERY_FILE.read_text(encoding="utf-8")

    log("Matérialisation des inférences evo:previousVersion ...")
    log(f"  Endpoint SPARQL Update : {UPDATE_URL}")
    log("  Validation post-inférence : activée")

    update_started_at = time.perf_counter()
    post_update(sparql_update)
    update_elapsed = round(time.perf_counter() - update_started_at, 3)
    log(f"Triplets evo:previousVersion insérés dans <{GRAPH_INFERRED}>")

    terms_old = load_terms(GRAPH_OLD)
    terms_new = load_terms(GRAPH_NEW)
    links = load_inferred_links()
    analysis = compute_metrics(terms_old, terms_new, links)

    payload = {
        "generated_at_epoch": int(time.time()),
        "dataset": FUSEKI_DATASET,
        "query_file": str(QUERY_FILE),
        "graph_uris": {
            "old": GRAPH_OLD,
            "new": GRAPH_NEW,
            "inferred": GRAPH_INFERRED,
        },
        "timing": {
            "update_elapsed_seconds": update_elapsed,
            "total_elapsed_seconds": round(time.perf_counter() - started_at, 3),
        },
        **analysis,
    }

    output_path = write_metrics(payload)
    log(f"Métriques sauvegardées : {output_path}")
    log(
        "Résumé : "
        f"{payload['metrics']['required_project_metrics']['classes_old_version_count']} classes anciennes, "
        f"{payload['metrics']['required_project_metrics']['classes_new_version_count']} classes dans la version récente, "
        f"{payload['metrics']['required_project_metrics']['new_classes_count']} nouvelles, "
        f"{payload['metrics']['additional_metrics']['inferred_previous_version_links_count']} liens previousVersion."
    )

    if not payload["validation_passed"]:
        log("ERREUR : la validation post-inference a echoue. Voir le fichier JSON des metriques.")
        return 1

    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    MARKER.touch()
    log(f"Terminé. Marqueur créé : {MARKER}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        log(f"ERREUR HTTP : {exc}")
        raise SystemExit(1) from exc
