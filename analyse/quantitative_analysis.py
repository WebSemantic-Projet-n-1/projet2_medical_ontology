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

import sys
from pathlib import Path
from typing import Dict, Set

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_ontologies import GO_NS, PATH_GO_NEW, PATH_GO_OLD, load_ontology

# Dossier de résultats : result/analyse
RESULTS_DIR = Path(__file__).resolve().parent / "result" / "quantitative"

# ---------------------------------------------------------------------------
# Domaine choisi : Réparation de l'ADN (DNA repair)
# ---------------------------------------------------------------------------
DOMAIN_ROOT_ID = "GO:0006281"
DOMAIN_LABEL = "DNA repair"


def go_id_to_iri(go_id: str) -> str:
    """Convertit un identifiant GO (ex. 'GO:0006281') en IRI OBO complète."""
    return GO_NS + go_id.replace(":", "_")


def get_descendants(onto, root_go_id: str) -> Set[str]:
    """Retourne les IRI de toutes les classes descendantes de root_go_id
    (racine incluse) par parcours BFS sur subclasses().
    """
    root_iri = go_id_to_iri(root_go_id)
    root_cls = onto.search_one(iri=root_iri)
    if root_cls is None:
        print(f"  [WARN] Classe racine {root_go_id} introuvable dans l'ontologie.")
        return set()

    visited: Set[str] = set()
    stack = [root_cls]
    while stack:
        # FILO
        cls = stack.pop()
        if cls.iri in visited:
            continue
        visited.add(cls.iri)
        for sub in cls.subclasses():
            if sub.iri not in visited:
                stack.append(sub)
    return visited


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

    print("Chargement de l'ontologie GO oct. 2025 …")
    onto_old = load_ontology(PATH_GO_OLD)

    print("Chargement de l'ontologie GO jan. 2026 …")
    onto_new = load_ontology(PATH_GO_NEW)

    # ------------------------------------------------------------------
    # 1. Ensembles de descendants dans chaque version
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

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "quantitative_stats.csv"
    df.to_csv(out_path, index=True)
    print(f"\nResultats exportes vers {out_path}")


if __name__ == "__main__":
    main()
