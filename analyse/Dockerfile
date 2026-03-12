## Dockerfile pour la partie analyse (raisonneur OWL)
##
## Contexte d'utilisation :
## - On lance les commandes Docker depuis le dossier `analyse/`.
## - Le build utilise le dossier racine du projet comme contexte (`..` dans
##   le docker-compose), ce qui permet de copier `analyse/` et `util/` dans
##   l'image tout en montant `../data` en volume.
##
## Image de base : Eclipse Temurin JDK 25 sur Ubuntu 24.04 (Noble).
## Java 25 est requis pour le JAR Jena utilisé par Pellet (class file 69.0).

FROM eclipse-temurin:25-jdk-noble

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Venv pour éviter le blocage PEP 668 (Ubuntu 24.04 "externally managed").
RUN python3 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Dépendances minimales pour reasoner_analysis.py
COPY analyse/requirements-reasoner.txt ./requirements-reasoner.txt
RUN pip install --no-cache-dir -r requirements-reasoner.txt

# Code source : on copie le dossier analyse/ et util/ de la racine du projet.
COPY analyse/ ./analyse/
COPY util/    ./util/

# Volumes :
# - /app/data            → fichiers OWL Gene Ontology (lecture seule)
# - /app/analyse/result  → rapports produits par le script (écriture)
VOLUME ["/app/data"]
VOLUME ["/app/analyse/result"]

CMD ["python", "analyse/reasoner_analysis.py"]

