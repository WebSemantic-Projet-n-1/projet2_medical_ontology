#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 1 : Chargement des ontologies GO (deux versions).

STRUCTURE DU SCRIPT
-------------------
1. Configuration des chemins vers les fichiers OWL (ancienne et récente version).
2. Chargement via rdflib ou owlready2.
3. Exploration de la structure : nombre de classes, propriétés, axiomes.
4. Sortie : résumé (console ou fichier) pour documenter l’analyse.

VARIABLES / CONSTANTES À DÉFINIR
--------------------------------
- PATH_GO_OLD : chemin vers le fichier OWL de l’ancienne version (ex. octobre 2025).
- PATH_GO_NEW : chemin vers le fichier OWL de la nouvelle version (ex. janvier 2026).
- (Optionnel) namespace GO : http://purl.obolibrary.org/obo/
- (Optionnel) domaine cible : GO:0006281 (DNA repair) ou GO:0012501 (apoptose) ou GO:0006629 (lipid metabolism).

DÉPENDANCES
-----------
- rdflib et/ou owlready2 (voir requirements.txt à la racine).

DEVICE (CUDA / CPU)
-------------------
Pour toute étape pouvant utiliser le GPU (ex. traitements batch lourds, embeddings),
utiliser : from util.device import get_device ; device = get_device().
Priorité CUDA, repli CPU automatique si indisponible.
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd
from owlready2 import World

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Version ancienne (octobre 2025) et récente (janvier 2026)
PATH_GO_OLD = DATA_DIR / "gene-ontology-10-25" / "data" / "ontology" / "go.owl"
PATH_GO_NEW = DATA_DIR / "gene-ontology-01-26" / "data" / "ontology" / "go.owl"

GO_NS = "http://purl.obolibrary.org/obo/"


def load_ontology(path: Path):
    """Charge une ontologie OWL dans un World owlready2 isolé.
  
    Chaque appel crée un World indépendant, ce qui évite les conflits d'IRI
    lorsqu'on charge deux versions du même fichier (ex. deux releases de GO)
    dans le même processus Python.
    """
    world = World()
    return world.get_ontology(str(path)).load()
  
  
def get_stats(onto, label: str, source_path: Path) -> Dict[str, Any]:
    """Retourne les statistiques structurées d'une ontologie owlready2."""
    num_classes = len(list(onto.classes()))
  
    num_obj_props = len(list(onto.object_properties()))
    num_data_props = len(list(onto.data_properties()))
    num_annotation_props = len(list(onto.annotation_properties()))
    num_properties = num_obj_props + num_data_props + num_annotation_props
  
    try:
      num_axioms = len(list(onto.axioms()))
    except Exception:
      num_axioms = None
    if num_axioms is None:
      try:
        w = onto.world
        rdfs = "http://www.w3.org/2000/01/rdf-schema#"
        owl_ns = "http://www.w3.org/2002/07/owl#"
        total = 0
        for pred in (f"<{rdfs}subClassOf>", f"<{owl_ns}equivalentClass>", f"<{owl_ns}disjointWith>"):
          rows = list(w.sparql(f"SELECT (COUNT(*) AS ?n) {{ ?s {pred} ?o . }}"))
          if rows and rows[0]:
            total += int(rows[0][0])
        num_axioms = total if total else None  # SubClassOf + EquivalentClasses + DisjointWith (≈ Protégé Logical)
      except Exception:
        pass
  
    try:
      num_individuals = len(list(onto.individuals()))
    except Exception:
      num_individuals = None
  
    return {
        "label": label,
        "fichier_owl": str(source_path),
        "nb_classes": num_classes,
        "proprietes": {
            "total": num_properties,
            "object_properties": num_obj_props,
            "data_properties": num_data_props,
            "annotation_properties": num_annotation_props,
        },
        "nb_axiomes": num_axioms,
        "nb_individus": num_individuals,
    }
  
  
def main() -> None:
    """Charge les deux versions de GO, affiche et exporte les statistiques."""
    print(f"Ancienne ontologie (octobre 2025) : {PATH_GO_OLD}")
    print(f"Nouvelle ontologie (janvier 2026)  : {PATH_GO_NEW}")
  
    onto_old = load_ontology(PATH_GO_OLD)
    onto_new = load_ontology(PATH_GO_NEW)
  
    stats_old = get_stats(onto_old, "GO_10-25", PATH_GO_OLD)
    stats_new = get_stats(onto_new, "GO_01-26", PATH_GO_NEW)
  
    # Affichage console
    rows = {
        "nb_classes": [stats_old["nb_classes"], stats_new["nb_classes"]],
        "nb_proprietes": [stats_old["proprietes"]["total"], stats_new["proprietes"]["total"]],
        "nb_axiomes": [stats_old["nb_axiomes"], stats_new["nb_axiomes"]],
        "nb_individus": [stats_old["nb_individus"], stats_new["nb_individus"]],
    }
    df = pd.DataFrame(rows, index=["GO_10-25", "GO_01-26"])
    print("\nRésumé des ontologies GO :")
    print(df.to_string())
  
if __name__ == "__main__":
    main()