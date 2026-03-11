# INF6253 – Projet 2 : Évolution des ontologies biomédicales

Extension de navigateur pour la veille sémantique sur Gene Ontology (GO).  
Hiver 2026.

---

## 1. Contexte et objectifs

- **Contexte** : Gene Ontology évolue continuellement (nouvelles classes, hiérarchies, dépréciations). Ce projet aide à naviguer dans ces changements.
- **Objectifs** :
  1. Analyser deux versions de GO (ex. janvier 2026 vs octobre 2025).
  2. Modéliser les versions en RDF/OWL et les charger dans un triplestore.
  3. Développer un service web d’analyse (API REST).
  4. Créer une extension de navigateur qui enrichit les pages GO (QuickGO, AmiGO, OLS) avec des infos d’évolution.

---

## 2. Structure du projet (livrable)

```
projet2_medical_ontology/
├── README.md              # Ce fichier
├── README.txt             # Copie pour soumission (instructions courtes)
├── requirements.txt       # Dépendances Python de base (sans PyTorch)
├── requirements-cuda.txt  # PyTorch avec CUDA (à installer en priorité si GPU dispo)
├── requirements-cpu.txt   # PyTorch CPU uniquement (repli si pas de CUDA)
├── data/                  # Fichiers OWL GO (à télécharger, voir data/README.md)
├── util/                  # Utilitaires partagés (détection device CUDA/CPU)
│   ├── __init__.py
│   └── device.py
├── analyse/               # Partie 1 : scripts d’analyse comparative GO
│   ├── README.md
│   ├── load_ontologies.py
│   ├── quantitative_analysis.py
│   ├── qualitative_analysis.py
│   └── reasoner_analysis.py
├── service-web/          # Partie 2 : API d’analyse
│   ├── README.md
│   ├── requirements.txt
│   ├── openapi.yaml
│   └── app/
├── extension-chrome/      # Partie 3 : extension Chrome (Manifest V3)
├── extension-firefox/     # Partie 3 : extension Firefox (optionnel)
└── triplestore/           # Config et données pour Jena Fuseki / GraphDB
```

---

## 3. Environnement de développement

### 3.1 Prérequis

- **Python** : 3.10+ (recommandé 3.11 ou 3.12).
- **OS** : Linux ou Windows.
- **CUDA** (prioritaire) : pilote NVIDIA + toolkit CUDA 11.8 ou 12.x pour utiliser le GPU. Sinon, le projet utilise le CPU automatiquement.
- **Optionnel** : Docker pour triplestore (Jena Fuseki ou GraphDB).

### 3.2 Environnement virtuel (venv) – CUDA en priorité, puis CPU

Le projet utilise un **venv local**. On installe **d’abord PyTorch avec CUDA** ; si l’installation échoue ou si aucun GPU n’est disponible, on bascule sur **PyTorch CPU**.

**Linux / macOS :**

```bash
cd /chemin/vers/projet2_medical_ontology
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# 1) Dépendances de base (rdflib, owlready2, SPARQL, etc.)
pip install -r requirements.txt

# 2) PyTorch : CUDA en priorité (Linux avec NVIDIA)
pip install -r requirements-cuda.txt
# Si erreur (pas de CUDA, driver manquant, etc.) → repli CPU :
# pip install -r requirements-cpu.txt

# 3) Service web
pip install -r service-web/requirements.txt
```

**Windows (PowerShell ou CMD) :**

```cmd
cd C:\chemin\vers\projet2_medical_ontology
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip

pip install -r requirements.txt
pip install -r requirements-cuda.txt
REM Si échec (pas de GPU / CUDA non installé) :
REM pip install -r requirements-cpu.txt

pip install -r service-web\requirements.txt
```

**Windows (Git Bash) :** `source .venv/Scripts/activate` puis les mêmes commandes `pip`.

### 3.3 Vérifier CUDA vs CPU

Après installation, dans le venv :

```bash
python -c "from util.device import get_device; print(get_device())"
```

- Affiche `cuda` (ou `cuda:0`) si PyTorch voit le GPU.
- Affiche `cpu` en repli (pas de GPU, driver manquant, ou PyTorch CPU installé).

### 3.4 Choix manuel CUDA 11.8 / 12.1 / 12.4

Par défaut, `requirements-cuda.txt` cible **CUDA 12.1** (compatible Linux et Windows). Si votre système a une autre version :

- **CUDA 11.8** : remplacer dans `requirements-cuda.txt` `cu121` par `cu118`.
- **CUDA 12.4** : remplacer par `cu124`.

Puis réinstaller : `pip install -r requirements-cuda.txt`.

### 3.5 Repli CPU (sans GPU)

Sur une machine sans NVIDIA ou si vous préférez tout en CPU :

```bash
pip install -r requirements.txt
pip install -r requirements-cpu.txt
pip install -r service-web/requirements.txt
```

Le code utilise `util.device.get_device()` : il choisit **CUDA si disponible, sinon CPU**. Aucune modification de code n’est nécessaire pour passer de l’un à l’autre.

---

## 4. Données et domaines

- **GO** : deux versions (ex. janvier 2026, octobre 2025) depuis [Zenodo 18422732](https://zenodo.org/records/18422732).
- **Domaines suggérés** (un à choisir) :
  - Réparation de l’ADN (DNA repair) : GO:0006281
  - Apoptose : GO:0012501
  - Métabolisme des lipides : GO:0006629
- **Pages cibles pour l’extension** : QuickGO, AmiGO 2, OLS (voir énoncé).

---

## 5. Utilisation rapide

- **Partie 1 (analyse)** : exécuter les scripts dans `analyse/` après téléchargement des OWL (voir `analyse/README.md`). Pour toute étape pouvant utiliser le GPU (ex. traitements batch, embeddings), les scripts s’appuient sur `util.device` (CUDA prioritaire, CPU en repli).
- **Partie 2 (service web)** : lancer l’API depuis `service-web/` (voir `service-web/README.md`), triplestore devant être démarré (voir `triplestore/README.md`).
- **Partie 3 (extension)** : charger le dossier `extension-chrome/` (ou `extension-firefox/`) en mode “développement” dans Chrome/Firefox.

---

## 6. Livrable Moodle

- **Nom du fichier** : `INF6253-P2-EquipeN.zip` (N = numéro/lettre du groupe).
- **Contenu** : code source, `README.txt`, rapport PDF. Structure détaillée dans l’énoncé du projet.
- **Date limite** : 29 mars 2026, 23h59.

---

## 7. Références

- Gene Ontology : <https://geneontology.org/docs/>
- OWL 2 : <https://www.w3.org/TR/owl2-overview/>
- SPARQL 1.1 : <https://www.w3.org/TR/sparql11-query/>
- WebExtensions : <https://developer.mozilla.org/fr/docs/Mozilla/Add-ons/WebExtensions>
- rdflib : <https://rdflib.readthedocs.io/>
- owlready2 : <https://owlready2.readthedocs.io/>
- PyTorch (CUDA / CPU) : <https://pytorch.org/get-started/locally/>
- Apache Jena Fuseki : <https://jena.apache.org/documentation/fuseki2/>
- GraphDB : <https://graphdb.ontotext.com/>
