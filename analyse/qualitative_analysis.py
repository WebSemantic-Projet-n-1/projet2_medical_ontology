#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 3 : Analyse qualitative sur 5 termes du domaine.

STRUCTURE DU SCRIPT
-------------------
1. Charger les deux versions de GO (comme dans load_ontologies).
2. Définir une liste de 5 identifiants GO du domaine (ex. DNA repair).
3. Pour chaque terme :
   - Comparer la définition (rdfs:comment) entre ancienne et nouvelle version.
   - Comparer la position dans la hiérarchie (parents directs).
   - Identifier les changements dans les relations (part-of, regulates, etc.).
4. Sortie : rapport texte ou structuré (JSON/Markdown) pour le rapport et les tableaux.

VARIABLES / CONSTANTES
----------------------
- TERM_IDS : liste de 5 GO IDs, ex. ["GO:0006281", "GO:0006284", ...].
- Namespaces : go:, rdfs:, owl:, et relations OBO (part_of, regulates, etc.).

DÉPENDANCES
-----------
- rdflib et/ou owlready2.

DEVICE (CUDA / CPU)
-------------------
Pour toute étape GPU (ex. similarité sémantique, embeddings) : from util.device import get_device.
Priorité CUDA, repli CPU.
"""

# TODO: imports et config (liste des 5 termes, chemins OWL)
# TODO: fonction get_definition(ontology, go_id) -> str
# TODO: fonction get_parents(ontology, go_id) -> list of (relation, parent_id)
# TODO: fonction get_relations(ontology, go_id) -> dict relation -> list of targets
# TODO: fonction compare_term(ontology_old, ontology_new, go_id) -> dict (definition_diff, hierarchy_diff, relations_diff)
# TODO: main : pour chaque terme, appeler compare_term et formater la sortie


def main() -> None:
    """Point d’entrée : comparaison qualitative des 5 termes."""
    pass  # À implémenter


if __name__ == "__main__":
    main()
