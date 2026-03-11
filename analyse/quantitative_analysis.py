#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 2 : Analyse quantitative du domaine choisi (ex. DNA repair).

STRUCTURE DU SCRIPT
-------------------
1. Réutiliser le chargement des deux versions (load_ontologies ou import).
2. Définir le domaine : racine GO (ex. GO:0006281) et ses descendants.
3. Pour chaque version, calculer :
   - Nombre de classes dans le domaine.
   - Nombre de classes nouvelles (présentes seulement dans la nouvelle version).
   - Nombre de classes dépréciées (owl:deprecated true).
   - Nombre de classes dont la hiérarchie a changé (parents différents entre les deux versions).
4. Sortie : tableaux / CSV / JSON pour le rapport et les graphiques.

VARIABLES / CONSTANTES
----------------------
- DOMAIN_ROOT : identifiant GO de la racine du domaine (ex. "GO:0006281").
- Réutilisation des chemins OWL et namespaces de load_ontologies.py (ou config partagée).

DÉPENDANCES
-----------
- rdflib et/ou owlready2 ; possiblement load_ontologies (refactoriser en module si besoin).

DEVICE (CUDA / CPU)
-------------------
Pour tout calcul intensif ou tensors : from util.device import get_device ; device = get_device().
Priorité CUDA, repli CPU si pas de GPU.
"""

# TODO: imports et config (domaine, chemins OWL)
# TODO: fonction get_descendants(ontology, root_go_id) -> set of class IRIs
# TODO: fonction count_deprecated(ontology, class_iris) -> int (owl:deprecated true)
# TODO: fonction count_hierarchy_changes(ontology_old, ontology_new, class_iris) -> int
# TODO: main : calculer les 4 métriques pour les deux versions, afficher/écrire résultats


def main() -> None:
    """Point d’entrée : calcul des statistiques quantitatives du domaine."""
    pass  # À implémenter


if __name__ == "__main__":
    main()
