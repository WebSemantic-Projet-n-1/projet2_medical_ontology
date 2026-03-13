#!/bin/sh
# Charge les deux versions OWL de Gene Ontology dans Apache Jena Fuseki
# via le Graph Store Protocol (HTTP PUT).
#
# Graphes nommés :
#   go:version/2025-10  →  http://purl.obolibrary.org/obo/go/version/2025-10
#   go:version/2026-01  →  http://purl.obolibrary.org/obo/go/version/2026-01
#
# Variables d'environnement utilisées (avec valeurs par défaut) :
#   FUSEKI_URL       – URL de base du serveur (défaut : http://fuseki:3030)
#   FUSEKI_DATASET   – Nom du dataset              (défaut : ds)
#   ADMIN_PASSWORD   – Mot de passe admin Fuseki    (défaut : admin)
#   DATA_DIR         – Répertoire racine des données (défaut : /data)
#   GRAPH_OLD_DIR    – Sous-répertoire version ancienne (défaut : gene-ontology-10-25/data/ontology)
#   GRAPH_NEW_DIR    – Sous-répertoire version nouvelle (défaut : gene-ontology-01-26/data/ontology)

set -e

FUSEKI_URL="${FUSEKI_URL:-http://fuseki:3030}"
DATASET="${FUSEKI_DATASET:-ds}"
PASSWORD="${ADMIN_PASSWORD:-admin}"

DATA_DIR="${DATA_DIR:-/data}"
GRAPH_OLD_DIR="${GRAPH_OLD_DIR:-gene-ontology-10-25/data/ontology}"
GRAPH_NEW_DIR="${GRAPH_NEW_DIR:-gene-ontology-01-26/data/ontology}"

GRAPH_OLD="http://purl.obolibrary.org/obo/go/version/2025-10"
GRAPH_NEW="http://purl.obolibrary.org/obo/go/version/2026-01"

FILE_OLD="${DATA_DIR}/${GRAPH_OLD_DIR}/go.owl"
FILE_NEW="${DATA_DIR}/${GRAPH_NEW_DIR}/go-basic.owl"

MARKER="/fuseki/.data-loaded"

# ── Idempotence ──────────────────────────────────────────────────────────────
if [ -f "$MARKER" ]; then
    echo "[loader] Les données sont déjà chargées ($MARKER trouvé). Abandon."
    exit 0
fi

# ── Vérification des fichiers source ─────────────────────────────────────────
MISSING=0
if [ ! -f "$FILE_OLD" ]; then
    echo "[loader] ATTENTION : fichier absent → $FILE_OLD"
    MISSING=1
fi
if [ ! -f "$FILE_NEW" ]; then
    echo "[loader] ATTENTION : fichier absent → $FILE_NEW"
    MISSING=1
fi

if [ "$MISSING" -eq 1 ]; then
    echo "[loader] Un ou plusieurs fichiers OWL manquent."
    echo "         Attendu : $FILE_OLD"
    echo "                   $FILE_NEW"
    echo "         Téléchargement : https://zenodo.org/records/18422732"
    exit 1
fi

# ── Chargement via HTTP Graph Store Protocol (PUT) ───────────────────────────
load_graph() {
    local file="$1"
    local graph="$2"
    local label="$3"
    local url="${FUSEKI_URL}/${DATASET}/data?graph=${graph}"

    echo "[loader] Chargement ${label} → ${graph}"
    echo "[loader]   Fichier  : ${file} ($(du -sh "$file" | cut -f1))"
    echo "[loader]   Endpoint : ${url}"

    curl --fail --silent --show-error \
        --user "admin:${PASSWORD}" \
        --request PUT \
        --header "Content-Type: application/rdf+xml" \
        --max-time 7200 \
        --data-binary "@${file}" \
        "${url}"

    echo "[loader] ✓ ${label} chargé."
}

load_graph "$FILE_OLD" "$GRAPH_OLD" "version 2025-10"
load_graph "$FILE_NEW" "$GRAPH_NEW" "version 2026-01"

# ── Marqueur d'idempotence ────────────────────────────────────────────────────
touch "$MARKER"
echo "[loader] Chargement terminé. Marqueur créé : $MARKER"
