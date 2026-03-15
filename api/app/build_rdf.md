# Pipeline build_rdf.py — Résultats d'exécution

## Commande exécutée

```bash
py api/app/build_rdf.py
```

---

## Logs d'exécution

```
2026-03-14 16:41:14  [INFO]  === Extraction version ancienne (2025-10) ===
2026-03-14 16:41:14  [INFO]  Chargement de data\gene-ontology-10-25\data\ontology\go-basic.owl ...
2026-03-14 16:42:29  [INFO]    1 265 006 triplets chargés.
2026-03-14 16:42:29  [INFO]    44 termes trouvés sous GO:0006281

2026-03-14 16:42:29  [INFO]  === Extraction version nouvelle (2026-01) ===
2026-03-14 16:42:29  [INFO]  Chargement de data\gene-ontology-01-26\data\ontology\go-basic.owl ...
2026-03-14 16:48:50  [INFO]    1 275 164 triplets chargés.
2026-03-14 16:48:50  [INFO]    46 termes trouvés sous GO:0006281

2026-03-14 16:48:50  [INFO]  === Génération des graphes RDF ===
2026-03-14 16:48:50  [INFO]    Graphe généré : 331 triplets pour 44 termes.
2026-03-14 16:48:50  [INFO]    Graphe généré : 347 triplets pour 46 termes.

2026-03-14 16:48:50  [INFO]  === Ajout des liens previousVersion ===
2026-03-14 16:48:50  [INFO]    43 liens evo:previousVersion ajoutés.

2026-03-14 16:48:50  [INFO]  Fichiers écrits :
                               output\go_dna_repair_2025-10.ttl
                               output\go_dna_repair_2026-01.ttl

2026-03-14 16:48:50  [INFO]  (Upload ignoré — relancez avec --upload pour envoyer à Fuseki.)
2026-03-14 16:48:50  [INFO]  === Terminé ===
```

---

## Pipeline de génération des fichiers .ttl

```
go-basic.owl
     │
     ▼
extract_terms()          ← trouve tous les descendants de GO:0006281
     │                      via rdfs:subClassOf
     │                      extrait : label, définition, parents,
     │                                deprecated, relations
     ▼
liste de dicts Python
     │
     ▼
to_evo_rdf()             ← convertit en triplets RDF
     │                      selon le vocabulaire evo:
     ▼
graphe rdflib en mémoire
     │
     ▼
g.serialize(format="turtle")
     │
     ├──► output/go_dna_repair_2025-10.ttl
     └──► output/go_dna_repair_2026-01.ttl
```

---

## Analyse des résultats

**Termes extraits par version**

- Version 2025-10 : **44 termes**
- Version 2026-01 : **46 termes**
- → **+2 termes nets** dans le domaine DNA repair (3 nouveaux, 1 disparu)

**Liens `evo:previousVersion` (43 sur 44)**

- 43 termes sont présents dans les deux versions → lien `previousVersion` créé
- 1 terme de 2025-10 est absent de 2026-01 → probablement déprécié ou fusionné
- 3 termes de 2026-01 sont nouveaux (46 − 43 = 3) → sans version précédente

---

## Résumé des chiffres

|                              | Version 2025-10 | Version 2026-01 |
|------------------------------|-----------------|-----------------|
| Triplets OWL chargés         | 1 265 006       | 1 275 164       |
| Termes DNA repair extraits   | 44              | 46              |
| Triplets RDF générés (evo:)  | 331             | 347             |
| Liens `evo:previousVersion`  | —               | 43              |
| Termes nouveaux              | —               | 3               |
| Termes disparus              | 1               | —               |


## Exemple requête SPARQL 

**http://localhost:3030/#/dataset/ds/query**

```
SELECT ?s ?p ?o
WHERE {
  GRAPH ?g {
    ?s ?p ?o
  }
}
LIMIT 10
```