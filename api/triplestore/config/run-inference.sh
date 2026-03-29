#!/bin/sh
# Exécute la matérialisation des inférences SPARQL dans Apache Jena Fuseki.
#
# Ce script utilise les capacités d'inférence du triplestore :
#   — lit les triplets evo:termID, evo:belongsToVersion, evo:versionDate
#   — génère automatiquement les liens evo:previousVersion
#   — stocke les triplets inférés dans le graphe <http://example.org/go/inferred>
#
# Variables d'environnement :
#   FUSEKI_URL       – URL de base du serveur   (défaut : http://fuseki:3030)
#   FUSEKI_DATASET   – Nom du dataset            (défaut : ds)
#   ADMIN_PASSWORD   – Mot de passe admin Fuseki  (défaut : admin)

set -e

FUSEKI_URL="${FUSEKI_URL:-http://fuseki:3030}"
DATASET="${FUSEKI_DATASET:-ds}"
PASSWORD="${ADMIN_PASSWORD:-admin}"

UPDATE_URL="${FUSEKI_URL}/${DATASET}/update"
QUERY_FILE="/sparql/materialize_previous_version.ru"
MARKER_DIR="${MARKER_DIR:-/marker}"
MARKER="${MARKER_DIR}/.inference-done"

# ── Idempotence ───────────────────────────────────────────────────────────────
if [ -f "$MARKER" ]; then
    echo "[inference] Inférences déjà matérialisées ($MARKER trouvé). Abandon."
    exit 0
fi

# ── Vérification du fichier SPARQL UPDATE ─────────────────────────────────────
if [ ! -f "$QUERY_FILE" ]; then
    echo "[inference] ERREUR : fichier SPARQL introuvable : $QUERY_FILE"
    exit 1
fi

echo "[inference] Matérialisation des inférences evo:previousVersion ..."
echo "[inference]   Endpoint SPARQL Update : ${UPDATE_URL}"
echo "[inference]   Règle : comparaison des evo:termID entre graphes nommés"

# ── Exécution du SPARQL UPDATE via HTTP POST ──────────────────────────────────
curl --fail --silent --show-error \
    --user "admin:${PASSWORD}" \
    --request POST \
    --header "Content-Type: application/sparql-update" \
    --data-binary "@${QUERY_FILE}" \
    "${UPDATE_URL}"

echo "[inference] Triplets evo:previousVersion insérés dans <http://example.org/go/inferred>"

# ── Vérification du nombre de triplets inférés ────────────────────────────────
COUNT_QUERY='SELECT (COUNT(*) AS ?n) WHERE { GRAPH <http://example.org/go/inferred> { ?s <http://example.org/evolution/previousVersion> ?o } }'
COUNT=$(curl --silent \
    --user "admin:${PASSWORD}" \
    --header "Accept: application/sparql-results+json" \
    --get \
    --data-urlencode "query=${COUNT_QUERY}" \
    "${FUSEKI_URL}/${DATASET}/sparql" \
    | grep -o '"value":"[0-9]*"' | grep -o '[0-9]*' | head -1)

echo "[inference] ${COUNT} triplets evo:previousVersion inférés."

# ── Marqueur d'idempotence ────────────────────────────────────────────────────
if touch "$MARKER" 2>/dev/null; then
    echo "[inference] Terminé. Marqueur créé : $MARKER"
else
    echo "[inference] WARNING: impossible d'écrire le marqueur ($MARKER). Service terminé quand même."
fi
