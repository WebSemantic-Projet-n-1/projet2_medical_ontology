#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 2 - Script d’extraction OWL -> RDF et chargement dans le triplestore.

STRUCTURE
---------
1. Lire les chemins des deux fichiers OWL (ancienne et nouvelle version).
2. Parser chaque OWL avec rdflib ou owlready2.
3. Pour chaque terme du domaine choisi (ex. DNA repair, racine GO:0006281) :
   - Extraire métadonnées (label, definition, deprecated, parents, relations).
   - Générer des triplets selon le vocabulaire evo: (TermVersion, termID, version, label, definition, isDeprecated, parent, etc.).
4. Écrire les triplets dans des graphes nommés (version 2025-10, version 2026-01).
5. Option : envoyer les RDF au triplestore via HTTP (Fuseki PUT) ou script de chargement.

VOCABULAIRE (evo:)
------------------
- TermVersion, OntologyVersion
- termID, version, label, definition, isDeprecated, parent
- previousVersion, versionDate, releaseNotes
- Namespace : http://example.org/evolution/

DÉPENDANCES
-----------
- rdflib ou owlready2 ; SPARQLWrapper ou requests pour l’upload vers le triplestore.

DEVICE (CUDA / CPU)
-------------------
Pour tout traitement parallèle ou tensors (ex. embeddings) : from util.device import get_device.
Priorité CUDA, repli CPU.
"""

# TODO: imports (rdflib, Path, requests ou SPARQLWrapper)
# TODO: config (PATH_GO_OLD, PATH_GO_NEW, DOMAIN_ROOT, EVO_NS, GRAPH_OLD, GRAPH_NEW)
# TODO: def extract_terms(ontology_path, domain_root) -> list of term dicts
# TODO: def to_evo_rdf(term_dict, version_uri) -> Graph
# TODO: def load_into_triplestore(graph, named_graph_uri, endpoint) -> ...
# TODO: main : extraire les deux versions, générer les graphes, charger (ou écrire en fichier .ttl)
def main() -> None:
    pass

if __name__ == "__main__":
    main()
