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

# TODO: imports
# from pathlib import Path
# import rdflib  # ou from owlready2 import get_ontology

# TODO: chemins et namespaces
# PATH_GO_OLD = Path(__file__).resolve().parent.parent / "data" / "go_2025-10.owl"
# PATH_GO_NEW = Path(__file__).resolve().parent.parent / "data" / "go_2026-01.owl"
# GO_NS = "http://purl.obolibrary.org/obo/"

# TODO: fonction load_ontology(path) -> graph ou ontology object
# TODO: fonction get_stats(graph/ontology) -> dict avec nb classes, propriétés, axiomes
# TODO: main : charger les deux, afficher les stats, (optionnel) exporter en JSON/texte


def main() -> None:
    """Point d’entrée : chargement des deux versions et affichage de la structure."""
    pass  # À implémenter


if __name__ == "__main__":
    main()
