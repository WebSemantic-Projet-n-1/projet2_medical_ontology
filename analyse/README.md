# Partie 1 : Analyse comparative des versions de GO

## Rôle des scripts

| Script | Rôle |
|--------|------|
| `load_ontologies.py` | Charge les deux versions de GO et exporte les statistiques de base |
| `quantitative_analysis.py` | Analyse quantitative du domaine DNA repair (classes, évolutions) |
| `qualitative_analysis.py` | Analyse qualitative de 5 termes GO (définitions, hiérarchie, relations) |
| `reasoner_analysis.py` | Raisonnement OWL avec HermiT (cohérence, incohérences) |

## Prérequis

Avoir complété la section "Installation des données GO (setup)" du README, avec les deux versions de GO extraites dans `data/`.

## Exécution

> HermiT/Pellet sur GO (~52k classes) requiert Java 11+

### Scripts non-raisonneur (depuis la racine du projet)

```bash
# Activer le venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell

python analyse/load_ontologies.py
python analyse/quantitative_analysis.py
python analyse/qualitative_analysis.py
```

### Raisonneur HermiT — via Docker (méthode recommandée)

Depuis le dossier `analyse/` :

```bash
cd analyse

# Premier lancement : build de l'image (~2 min)
docker compose build reasoner

# Lancer l'analyse (HermiT sur les deux versions GO)
docker compose run --rm reasoner
```

L'image embarque Java 25 et lance la JVM avec **`-Xmx4000M`** (4 Go de heap).
Prend environ 2 minutes par dataset.