#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# inspiré du fichier users.ttl metadata
"""
Partie 2 - Script d'extraction OWL -> RDF et chargement dans le triplestore.

STRUCTURE
---------
1. Lire les chemins des deux fichiers OWL (ancienne et nouvelle version).
2. Parser chaque OWL avec rdflib.
3. Pour chaque terme du domaine choisi (DNA repair, racine GO:0006281) :
   - Extraire métadonnées (label, definition, deprecated, parents, relations).
   - Générer des triplets selon le vocabulaire evo:.
4. Écrire les triplets dans des graphes nommés (version 2025-10, version 2026-01).
5. Option : envoyer les RDF au triplestore via HTTP (Fuseki PUT).

VOCABULAIRE (evo:)
------------------
- TermVersion, OntologyVersion
- termID, version, label, definition, isDeprecated, parent
- previousVersion, versionDate, releaseNotes
- Namespace : http://example.org/evolution/

DÉPENDANCES
-----------
    pip install rdflib requests

UTILISATION
-----------
    python build_rdf.py
    python build_rdf.py --upload   # pour envoyer au triplestore Fuseki
"""
import os
from dotenv import load_dotenv
import argparse
import logging
from pathlib import Path

import requests
from rdflib import RDF, OWL, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDFS, XSD

# ───
# CONFIG
# ───

# Chemins fichiers OWL dossier data / Ancien et nouveau
PATH_GO_OLD = Path("data/gene-ontology-10-25/data/ontology/go-basic.owl") # 10 - 2025
PATH_GO_NEW = Path("data/gene-ontology-01-26/data/ontology/go-basic.owl") # 01 - 2026

# Racine du domaine étudié : DNA repair
DOMAIN_ROOT = "http://purl.obolibrary.org/obo/GO_0006281"

# Namespaces / l'EVO n'a pas besoin d'une réel url
EVO_NS   = Namespace("http://example.org/evolution/")
GO_NS    = Namespace("http://purl.obolibrary.org/obo/")
OBO_NS   = Namespace("http://purl.obolibrary.org/obo/")

# URIs des graphes nommés dans le triplestore
GRAPH_OLD = URIRef("http://example.org/go/version/2025-10")
GRAPH_NEW = URIRef("http://example.org/go/version/2026-01")

# Endpoint Fuseki
FUSEKI_ENDPOINT = "http://localhost:3030/ds"

# Dates de publication
VERSION_DATE_OLD = "2025-10-01"
VERSION_DATE_NEW = "2026-01-15"

# ──────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# ÉTAPE 1 : Extraction des termes d'un domaine
# ──────────────────────────────────────────────────────────────

def extract_terms(ontology_path: Path, domain_root: str) -> list[dict]:
    """
    Parse un fichier OWL et extrait tous les termes descendants
    de domain_root (inclus), ainsi que leurs métadonnées.

    Paramètres
    ----------
    ontology_path : chemin vers le fichier .owl
    domain_root   : URI du terme racine (ex: GO:0006281)

    Retourne
    --------
    Liste de dicts avec les clés :
        uri, term_id, label, definition, is_deprecated, parents, relations
    """
    log.info(f"Chargement de {ontology_path} ...")
    g = Graph()
    g.parse(str(ontology_path))
    log.info(f"  {len(g)} triplets chargés.")

    root_uri = URIRef(domain_root)

    # Récupère tous les descendants de domain_root (subClassOf transitif)
    descendants = _get_descendants(g, root_uri)
    descendants.add(root_uri)
    log.info(f"  {len(descendants)} termes trouvés sous {domain_root}")

    terms = []
    for class_uri in descendants:
        term = _extract_single_term(g, class_uri)
        if term:
            terms.append(term)

    return terms


def _get_descendants(g: Graph, root: URIRef) -> set:
    """
    Retourne tous les descendants d'une classe via rdfs:subClassOf (transitif).
    On utilise une recherche en largeur (BFS) pour éviter la récursion.
    """
    visited = set()
    queue   = [root]

    while queue:
        current = queue.pop(0)
        for child in g.subjects(RDFS.subClassOf, current):
            if child not in visited and isinstance(child, URIRef):
                visited.add(child)
                queue.append(child)

    return visited


def _extract_single_term(g: Graph, class_uri: URIRef) -> dict | None:
    """
    Extrait les métadonnées d'un terme GO depuis le graphe RDF.
    Retourne None si le terme n'est pas une vraie classe GO.
    """
    # Filtre : on garde seulement les vraies classes OWL (pas les blank nodes)
    if (class_uri, RDF.type, OWL.Class) not in g:
        return None

    # Identifiant GO (ex: "GO:0006281")
    local = str(class_uri).split("/")[-1]          # "GO_0006281"
    term_id = local.replace("GO_", "GO:")          # "GO:0006281"

    # Label (rdfs:label)
    label = _get_literal(g, class_uri, RDFS.label)

    # Définition (obo:IAO_0000115 est la propriété standard dans GO)
    IAO_DEF = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")
    definition = _get_literal(g, class_uri, IAO_DEF)
    if not definition:
        # Fallback sur rdfs:comment
        definition = _get_literal(g, class_uri, RDFS.comment)

    # Dépréciation (owl:deprecated)
    deprecated_lit = g.value(class_uri, OWL.deprecated)
    is_deprecated = bool(deprecated_lit) and str(deprecated_lit).lower() == "true"

    # Parents directs (rdfs:subClassOf — seulement les URIRef, pas les blank nodes)
    parents = [
        str(p) for p in g.objects(class_uri, RDFS.subClassOf)
        if isinstance(p, URIRef)
    ]

    # Relations sémantiques GO (part_of, regulates, etc.) via blank nodes
    relations = _extract_relations(g, class_uri)

    return {
        "uri":           str(class_uri),
        "term_id":       term_id,
        "label":         label or "",
        "definition":    definition or "",
        "is_deprecated": is_deprecated,
        "parents":       parents,
        "relations":     relations,
    }


def _get_literal(g: Graph, subject: URIRef, predicate: URIRef) -> str | None:
    """Retourne la première valeur littérale d'un prédicat, ou None."""
    val = g.value(subject, predicate)
    return str(val) if val else None


def _extract_relations(g: Graph, class_uri: URIRef) -> list[dict]:
    """
    Extrait les relations sémantiques GO (part_of, regulates, etc.)
    encodées comme restrictions OWL (blank nodes avec owl:onProperty).
    """
    relations = []
    OWL_RESTRICTION = OWL.Restriction
    OWL_ON_PROPERTY = OWL.onProperty
    OWL_SOME_VALUES = OWL.someValuesFrom

    for parent in g.objects(class_uri, RDFS.subClassOf):
        if (parent, RDF.type, OWL_RESTRICTION) in g:
            prop   = g.value(parent, OWL_ON_PROPERTY)
            target = g.value(parent, OWL_SOME_VALUES)
            if prop and target and isinstance(target, URIRef):
                relations.append({
                    "property": str(prop),
                    "target":   str(target),
                })
    return relations


# ──────────────────────────────────────────────────────────────
# ÉTAPE 2 : Conversion en triplets RDF (vocabulaire evo:)
# ──────────────────────────────────────────────────────────────

def to_evo_rdf(terms: list[dict], version_uri: URIRef, version_date: str) -> Graph:
    """
    Convertit une liste de termes extraits en un graphe RDF
    utilisant le vocabulaire evo:.

    Paramètres
    ----------
    terms        : liste de dicts produits par extract_terms()
    version_uri  : URI de la version (ex: GRAPH_OLD)
    version_date : date ISO (ex: "2025-10-01")

    Retourne
    --------
    Un graphe rdflib prêt à être sérialisé ou chargé dans Fuseki.
    """
    g = Graph()
    g.bind("evo",  EVO_NS)
    g.bind("go",   GO_NS)
    g.bind("owl",  OWL)
    g.bind("rdfs", RDFS)
    g.bind("xsd",  XSD)

    # ── Instance de OntologyVersion ──
    g.add((version_uri, RDF.type,            EVO_NS.OntologyVersion))
    g.add((version_uri, EVO_NS.versionDate,  Literal(version_date, datatype=XSD.date)))

    # ── Un TermVersion par terme ──
    for term in terms:
        # URI unique par terme + version  ex: .../GO_0006281/2025-10
        version_slug = str(version_uri).split("/")[-1]   # "2025-10"
        local_id     = term["term_id"].replace("GO:", "GO_")
        term_ver_uri = URIRef(f"http://example.org/evolution/term/{local_id}/{version_slug}")

        g.add((term_ver_uri, RDF.type,               EVO_NS.TermVersion))
        g.add((term_ver_uri, EVO_NS.termID,          Literal(term["term_id"], datatype=XSD.string)))
        g.add((term_ver_uri, EVO_NS.label,           Literal(term["label"], lang="en")))
        g.add((term_ver_uri, EVO_NS.definition,      Literal(term["definition"], lang="en")))
        g.add((term_ver_uri, EVO_NS.isDeprecated,    Literal(term["is_deprecated"], datatype=XSD.boolean)))
        g.add((term_ver_uri, EVO_NS.belongsToVersion, version_uri))

        # Parents directs
        for parent_uri_str in term["parents"]:
            parent_local = parent_uri_str.split("/")[-1]
            parent_ver   = URIRef(f"http://example.org/evolution/term/{parent_local}/{version_slug}")
            g.add((term_ver_uri, EVO_NS.hasParent, parent_ver))

        # Relations sémantiques (part_of, regulates, etc.)
        for rel in term["relations"]:
            target_local = rel["target"].split("/")[-1]
            target_ver   = URIRef(f"http://example.org/evolution/term/{target_local}/{version_slug}")
            prop_uri     = URIRef(rel["property"])
            g.add((term_ver_uri, prop_uri, target_ver))

    log.info(f"  Graphe généré : {len(g)} triplets pour {len(terms)} termes.")
    return g


# ──────────────────────────────────────────────────────────────
# ÉTAPE 3 : Enrichissement — liens previousVersion entre versions
# ──────────────────────────────────────────────────────────────

def add_previous_version_links(g_old: Graph, g_new: Graph) -> Graph:
    """
    Compare les deux graphes et ajoute les triplets evo:previousVersion
    pour chaque terme présent dans les deux versions.

    Paramètres
    ----------
    g_old : graphe de l'ancienne version
    g_new : graphe de la nouvelle version (modifié en place)

    Retourne
    --------
    g_new enrichi avec les liens previousVersion.
    """
    # Collecte les termID de chaque version
    old_terms = {}
    for s in g_old.subjects(RDF.type, EVO_NS.TermVersion):
        tid = g_old.value(s, EVO_NS.termID)
        if tid:
            old_terms[str(tid)] = s

    new_terms = {}
    for s in g_new.subjects(RDF.type, EVO_NS.TermVersion):
        tid = g_new.value(s, EVO_NS.termID)
        if tid:
            new_terms[str(tid)] = s

    count = 0
    for term_id, new_uri in new_terms.items():
        if term_id in old_terms:
            g_new.add((new_uri, EVO_NS.previousVersion, old_terms[term_id]))
            count += 1

    log.info(f"  {count} liens evo:previousVersion ajoutés.")
    return g_new


# ──────────────────────────────────────────────────────────────
# ÉTAPE 4 : Chargement dans le triplestore Fuseki
# ──────────────────────────────────────────────────────────────

def load_into_triplestore(g: Graph, named_graph_uri: URIRef, endpoint: str) -> bool:
    """
    Envoie un graphe RDF vers un graphe nommé dans Apache Jena Fuseki
    via une requête HTTP PUT.

    Paramètres
    ----------
    g               : graphe rdflib à envoyer
    named_graph_uri : URI du graphe nommé cible
    endpoint        : URL de base du dataset Fuseki

    Retourne
    --------
    True si succès, False sinon.
    """
    ttl_data = g.serialize(format="turtle")
    url      = f"{endpoint}/data"
    params   = {"graph": str(named_graph_uri)}
    headers  = {"Content-Type": "text/turtle; charset=utf-8"}
    password = os.getenv("ADMIN_PASSWORD", "admin")

    log.info(f"  Envoi vers {url} (graphe: {named_graph_uri}) ...")
    try:
        response = requests.put(
            url,
            data=ttl_data.encode("utf-8"),
            params=params,
            headers=headers,
            auth=("admin", password),
            timeout=30
        )
        response.raise_for_status()
        log.info(f"  Chargement réussi (HTTP {response.status_code}).")
        return True
    except requests.RequestException as e:
        log.error(f"  Échec du chargement : {e}")
        return False


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extraction OWL -> RDF (vocabulaire evo:) pour Gene Ontology."
    )
    parser.add_argument(
        "--upload", action="store_true",
        help="Envoyer les graphes vers Fuseki après génération."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output"),
        help="Dossier de sortie pour les fichiers .ttl (défaut: ./output)."
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Extraction ──────────────────────────────────────────
    log.info("=== Extraction version ancienne (2025-10) ===")
    terms_old = extract_terms(PATH_GO_OLD, DOMAIN_ROOT)

    log.info("=== Extraction version nouvelle (2026-01) ===")
    terms_new = extract_terms(PATH_GO_NEW, DOMAIN_ROOT)

    # ── 2. Génération RDF ─────────────────────────────────────
    log.info("=== Génération des graphes RDF ===")
    g_old = to_evo_rdf(terms_old, GRAPH_OLD, VERSION_DATE_OLD)
    g_new = to_evo_rdf(terms_new, GRAPH_NEW, VERSION_DATE_NEW)

    # ── 3. Enrichissement previousVersion ─────────────────────
    log.info("=== Ajout des liens previousVersion ===")
    g_new = add_previous_version_links(g_old, g_new)

    # ── 4. Sauvegarde locale en .ttl ──────────────────────────
    path_old = args.output_dir / "go_dna_repair_2025-10.ttl"
    path_new = args.output_dir / "go_dna_repair_2026-01.ttl"

    g_old.serialize(destination=str(path_old), format="turtle")
    g_new.serialize(destination=str(path_new), format="turtle")
    log.info(f"  Fichiers écrits : {path_old}, {path_new}")

    # ── 5. Upload vers Fuseki (optionnel) ─────────────────────
    if args.upload:
        log.info("=== Chargement dans Fuseki ===")
        load_into_triplestore(g_old, GRAPH_OLD, FUSEKI_ENDPOINT)
        load_into_triplestore(g_new, GRAPH_NEW, FUSEKI_ENDPOINT)
    else:
        log.info("(Upload ignoré — relancez avec --upload pour envoyer à Fuseki.)")

    log.info("=== Terminé ===")


if __name__ == "__main__":
    main()