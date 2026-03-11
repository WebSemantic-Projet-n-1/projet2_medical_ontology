#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 4 : Utilisation d’un raisonneur OWL (HermiT, Pellet).

STRUCTURE DU SCRIPT
-------------------
1. Charger une version de GO (ou les deux, en deux runs).
2. Lancer un raisonneur sur l’ontologie :
   - HermiT ou Pellet sont souvent utilisés via Protégé ou via des bindings Java (jpype, py4j).
   - Alternative : utiliser owlready2 si un raisonneur est intégré (voir doc owlready2).
3. Mesurer le temps de raisonnement.
4. Récupérer et noter d’éventuelles incohérences (inconsistent classes, etc.).
5. Répéter pour l’autre version et comparer les temps / incohérences.

NOTE IMPORTANTE
---------------
Les raisonneurs OWL complets (HermiT, Pellet) sont typiquement en Java. Options :
- Exécuter le raisonnement dans Protégé et documenter manuellement les temps et résultats.
- Ou utiliser owlready2 avec un raisonneur supporté (si disponible).
- Ou appeler un service externe / sous-process Java et parser la sortie.
Ce script peut donc se contenter de :
- Charger l’ontologie,
- Appeler un sous-process (ex. robot/java) ou documenter la procédure manuelle,
- Lire un fichier de résultats pré-généré et afficher un résumé.

DÉPENDANCES
-----------
- owlready2 (et éventuellement Java en PATH si on appelle un outil externe).

DEVICE (CUDA / CPU)
-------------------
Si raisonnement ou post-traitement utilise PyTorch : from util.device import get_device.
Priorité CUDA, repli CPU.
"""

# TODO: imports et config (chemins OWL)
# TODO: fonction run_reasoner(ontology_path) -> dict avec elapsed_time_seconds, inconsistencies (list)
# TODO: main : run sur ancienne et nouvelle version, afficher tableau comparatif


def main() -> None:
    """Point d’entrée : raisonnement sur les deux versions et rapport des temps / incohérences."""
    pass  # À implémenter


if __name__ == "__main__":
    main()
