# Partie 1 : Analyse comparative des versions de GO

## Device : CUDA en priorité, repli CPU

Les scripts peuvent utiliser `util.device.get_device()` pour tout calcul PyTorch (traitements lourds, embeddings) : **CUDA** si disponible, sinon **CPU**. Exécuter depuis la **racine du projet** pour que l’import `from util.device import get_device` fonctionne.

## Rôle des scripts

| Script | Rôle |
|--------|------|
| `load_ontologies.py` | Charge les deux OWL (ancienne + récente) avec rdflib/owlready2 ; expose structure (classes, propriétés, axiomes). |
| `quantitative_analysis.py` | Pour le domaine choisi : nombre de classes, nouvelles, dépréciées, hiérarchie modifiée. |
| `qualitative_analysis.py` | Pour 5 termes : comparaison définitions (rdfs:comment), position hiérarchique, relations (part-of, regulates, etc.). |
| `reasoner_analysis.py` | Lance un raisonneur (HermiT/Pellet) sur chaque version ; temps de raisonnement et incohérences. |

## Données

- Télécharger les deux versions de GO (janvier 2026, octobre 2025) depuis [Zenodo 18422732](https://zenodo.org/records/18422732).
- Placer les fichiers OWL dans un dossier connu (ex. `../data/` ou chemin configurable).

## Exécution

Depuis la **racine du projet**, avec le venv activé (PyTorch : `requirements-cuda.txt` en priorité, `requirements-cpu.txt` en repli) :

```bash
python analyse/load_ontologies.py
python analyse/quantitative_analysis.py
python analyse/qualitative_analysis.py
python analyse/reasoner_analysis.py
```

Documenter les résultats (tableaux, graphiques) dans le rapport.
