INF6253 - Projet 2 - Evolution des ontologies biomedicales (Gene Ontology)
================================================================================

CONTENU DU LIVRABLE
-------------------
- rapport.pdf
- Ce README.txt
- analyse/          Scripts d'analyse Partie 1 (Python)
- service-web/      API REST (Flask/FastAPI), requirements.txt, openapi.yaml
- extension-chrome/ Extension Chrome (Manifest V3)
- extension-firefox/ Extension Firefox (optionnel)
- triplestore/      Configuration et donnees pour le triplestore
- util/             Utilitaire get_device() : CUDA si disponible, sinon CPU

INSTALLATION RAPIDE (Linux / Windows) - CUDA EN PRIORITE, PUIS CPU
-------------------------------------------------------------------
1. Python 3.10+ requis.
2. Creer un environnement virtuel :
   - Linux/macOS : python3 -m venv .venv && source .venv/bin/activate
   - Windows     : python -m venv .venv && .venv\Scripts\activate
3. Installer les dependances (priorite CUDA, repli CPU) :
   pip install -r requirements.txt
   pip install -r requirements-cuda.txt
   (Si echec : pip install -r requirements-cpu.txt)
   pip install -r service-web/requirements.txt
4. Verifier device : python -c "from util.device import get_device; print(get_device())"
   -> "cuda" ou "cuda:0" si GPU, "cpu" sinon.
5. Telecharger les deux versions de GO depuis Zenodo (voir README.md).
6. Configurer et demarrer le triplestore (voir triplestore/README.md).
7. Lancer le service web depuis service-web/ (voir service-web/README.md).
8. Charger l'extension : Chrome -> Extensions -> Charger l'extension non empaquetee -> extension-chrome/

DOCUMENTATION
-------------
Voir README.md pour la structure du projet, CUDA vs CPU, objectifs, references.

EQUIPE ET REMISE
----------------
Nom du fichier a remettre : INF6253-P2-EquipeN.zip (N = numero/lettre du groupe).
Date limite : 29 mars 2026 23h59 (Moodle).
