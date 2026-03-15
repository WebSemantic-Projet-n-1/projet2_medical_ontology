#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 2 : Analyse quantitative du domaine choisi (DNA repair).

STRUCTURE DU SCRIPT
-------------------
1. Réutiliser le chargement des deux versions via load_ontologies.
2. Définir le domaine : racine GO:0006281 (DNA repair) et ses descendants.
3. Pour chaque version, calculer :
   - Nombre de classes dans le domaine.
   - Nombre de classes nouvelles (présentes seulement dans la nouvelle version).
   - Nombre de classes dépréciées (owl:deprecated true).
   - Nombre de classes dont la hiérarchie a changé (parents directs différents).
4. Sortie : tableaux / CSV pour le rapport.
"""

from typing import Dict, Set
import pandas as pd
from load_ontologies import GO_NS, PATH_GO_NEW, PATH_GO_OLD, load_ontology

# ---------------------------------------------------------------------------
# Domaine choisi : Réparation de l'ADN (DNA repair)
# ---------------------------------------------------------------------------
DOMAIN_ROOT_ID = "GO:0006281"
DOMAIN_LABEL = "DNA repair"


def go_id_to_iri(go_id: str) -> str:
    """Convertit un identifiant GO (ex. 'GO:0006281') en IRI OBO complète."""
    return GO_NS + go_id.replace(":", "_")


def get_descendants(onto, root_go_id: str) -> Set[str]:
    """Retourne les IRI (str) de toutes les classes descendantes de root_go_id
    (racine incluse) via SPARQL 1.1 sur le world owlready2.

    Compte uniquement la hiérarchie is_a (rdfs:subClassOf), pas part_of/regulates.
    """
    root_iri = go_id_to_iri(root_go_id)
    try:
        q = (
            "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
            "SELECT DISTINCT ?sub WHERE { "
            "?sub rdfs:subClassOf* <%s> . "
            "FILTER(ISIRI(?sub)) }"
        ) % root_iri
        rows = list(onto.world.sparql(q))
        return {str(row[0]) for row in rows}
    except Exception as e:
        print(f"  [WARN] SPARQL descendants échoué pour {root_go_id}: {e}")
        return set()


def count_deprecated(onto, class_iris: Set[str]) -> int:
    """Compte les classes (parmi class_iris) marquées owl:deprecated true."""
    count = 0
    for cls in onto.classes():
        if cls.iri not in class_iris:
            continue
        dep = getattr(cls, "deprecated", None)
        if dep:
            count += 1
    return count


def get_direct_parents(cls) -> Set[str]:
    """Retourne les IRI des parents directs (is_a nommés) d'une classe owlready2.

    On ignore les restrictions anonymes (RestrictionClass) pour ne garder
    que les super-classes nommées, qui correspondent aux relations is_a OWL.
    """
    parents: Set[str] = set()
    for parent in cls.is_a:
        iri = getattr(parent, "iri", None)
        if iri:
            parents.add(iri)
    return parents


def count_hierarchy_changes(onto_old, onto_new, iris_common: Set[str]) -> int:
    """Compte les classes (parmi iris_common) dont les parents directs is_a
    diffèrent entre onto_old et onto_new.
    """
    # Index iri -> classe pour un accès O(1)
    old_index: Dict[str, object] = {
        cls.iri: cls for cls in onto_old.classes() if cls.iri in iris_common
    }
    new_index: Dict[str, object] = {
        cls.iri: cls for cls in onto_new.classes() if cls.iri in iris_common
    }

    changed = 0
    for iri in iris_common:
        cls_old = old_index.get(iri)
        cls_new = new_index.get(iri)
        if cls_old is None or cls_new is None:
            continue
        if get_direct_parents(cls_old) != get_direct_parents(cls_new):
            changed += 1
    return changed


def main() -> None:
    """Analyse quantitative du domaine sélectionné entre les deux versions GO."""
    print(f"Domaine analysé : {DOMAIN_ROOT_ID} ({DOMAIN_LABEL})")
    print(f"  Ancienne version (oct. 2025) : {PATH_GO_OLD}")
    print(f"  Nouvelle version (jan. 2026) : {PATH_GO_NEW}\n")

    print("Chargement de l'ontologie GO oct. 2025 (owlready2) …")
    onto_old = load_ontology(PATH_GO_OLD)

    print("Chargement de l'ontologie GO jan. 2026 (owlready2) …")
    onto_new = load_ontology(PATH_GO_NEW)

    # ------------------------------------------------------------------
    # 1. Ensembles de descendants dans chaque version (hiérarchie is_a)
    # ------------------------------------------------------------------
    print(f"\nExtraction des descendants de {DOMAIN_ROOT_ID} …")
    iris_old = get_descendants(onto_old, DOMAIN_ROOT_ID)
    iris_new = get_descendants(onto_new, DOMAIN_ROOT_ID)

    iris_added   = iris_new - iris_old   # nouvelles classes
    iris_removed = iris_old - iris_new   # supprimées / hors domaine
    iris_common  = iris_old & iris_new   # présentes dans les deux

    # ------------------------------------------------------------------
    # 2. Classes dépréciées
    # ------------------------------------------------------------------
    print("Comptage des classes dépréciées …")
    n_depr_old = count_deprecated(onto_old, iris_old)
    n_depr_new = count_deprecated(onto_new, iris_new)

    # ------------------------------------------------------------------
    # 3. Changements de hiérarchie (classes communes)
    # ------------------------------------------------------------------
    print("Détection des changements de hiérarchie …")
    n_hier_changed = count_hierarchy_changes(onto_old, onto_new, iris_common)

    # ------------------------------------------------------------------
    # 4. Synthèse
    # ------------------------------------------------------------------
    results = {
        "nb_classes_domaine":      [len(iris_old),    len(iris_new)],
        "nb_classes_nouvelles":    ["—",              len(iris_added)],
        "nb_classes_supprimées":   [len(iris_removed), "—"],
        "nb_deprecated":           [n_depr_old,       n_depr_new],
        "nb_hierarchie_changée":   ["—",              n_hier_changed],
    }

    df = pd.DataFrame(results, index=["GO_10-25", "GO_01-26"])

    print(f"\nResultats - domaine {DOMAIN_ROOT_ID} ({DOMAIN_LABEL}) :")
    print(df.to_string())


if __name__ == "__main__":
    main()
