# Partie 1 : Analyse comparative des versions de GO

## Rôle des scripts

| Script | Rôle |
|--------|------|
| `load_ontologies.py` | Charge les deux versions de GO et exporte les statistiques de base |
| `quantitative_analysis.py` | Analyse quantitative du domaine DNA repair (classes, évolutions) |
| `qualitative_analysis.py` | Analyse qualitative de 5 termes GO (définitions, hiérarchie, relations) |
| `reasoner_analysis.py` | Raisonnement OWL avec HermiT et Pellet (cohérence, incohérences) |

## Prérequis

Avoir complété la section "Installation des données GO (setup)" du README, avec les deux versions de GO extraites dans `data/`.

## Exécution

> HermiT/Pellet sur GO (~52k classes) requiert Java 25 et 12 Go de heap Java.

### Scripts non-raisonneur (depuis la racine du projet)

```bash
# Activer le venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows PowerShell

python analyse/load_ontologies.py
python analyse/quantitative_analysis.py
python analyse/qualitative_analysis.py
```

### Raisonneur HermiT / Pellet — via Docker (méthode recommandée)

Depuis le dossier `analyse/` :

```bash
cd analyse

# Premier lancement : build de l'image (~2 min)
docker compose build reasoner

# Lancer l'analyse (HermiT + Pellet sur les deux versions GO)
docker compose run --rm reasoner
```

L'image embarque Java 25 et lance la JVM avec **`-Xmx12000M`** (12 Go de heap).
Le conteneur est limité à **12 Go de RAM** (`mem_limit: 12g` dans `docker-compose.yml`).

> **Docker Desktop** : vérifiez que le moteur Docker dispose d'au moins 14 Go de RAM
> (Settings → Resources → Memory) pour absorber le heap + l'overhead JVM/OS.

Les rapports sont écrits dans `analyse/result/reasoner/` sur la machine hôte.

Prend environ 2 minutes pour HermiT sur oct-25.