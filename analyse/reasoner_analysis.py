#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 4 : Utilisation d'un raisonneur OWL (HermiT).

Lance HermiT sur les deux versions de Gene Ontology
(octobre 2025 et janvier 2026), domaine DNA repair (GO:0006281).

Prérequis
---------
- Java installé et accessible (détection automatique via PATH).
- HermiT : Java 11+
"""

import configparser
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import owlready2
from owlready2 import OwlReadyInconsistentOntologyError, World

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_ontologies import GO_NS, PATH_GO_NEW, PATH_GO_OLD

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "reasoner_config.ini"
RESULTS_DIR = SCRIPT_DIR / "result" / "reasoner"

# ---------------------------------------------------------------------------
# Domaine : DNA repair
# ---------------------------------------------------------------------------

DOMAIN_ROOT_ID = "GO:0006281"
DOMAIN_LABEL = "DNA repair"

REASONERS = ["HermiT"]

# ---------------------------------------------------------------------------
# Vérification et configuration de Java
# ---------------------------------------------------------------------------

def get_java_version(java_exe: str) -> str[str]:
    """Retourne (version_majeure, chaîne_version_complète).

    version_majeure vaut 0 si la version n'a pas pu être déterminée.
    """
    try:
        proc = subprocess.run(
            [java_exe, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = proc.stderr or proc.stdout
        first_line = output.strip().splitlines()[0] if output.strip() else ""

        match = re.search(r'"(\d+)[\.\-_]', first_line)
        if match:
            return first_line
        match = re.search(r'"(\d+)"', first_line)
        if match:
            return first_line
        return first_line
    except Exception as exc:
        return str(exc)


def get_java_malloc() -> Optional[int]:
    """Retourne la taille de heap JVM définie dans reasoner_config.ini, ou None."""
    if not CONFIG_PATH.exists():
        return None
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_PATH, encoding="utf-8")
    raw = cfg.get("java", "memory_mb", fallback="4096").strip()
    if not raw:
        return None
    try:
        val = int(raw)
        return val if val > 0 else None
    except ValueError:
        print(f"[WARN] Valeur memory_mb invalide dans {CONFIG_PATH.name}: {raw!r}")
        return None


def setup_java() -> bool:
    """Configure owlready2.JAVA_EXE et le heap JVM."""
    java = shutil.which("java")
    if not java:
        print("  ERREUR : Java introuvable sur ce système.")
        return False

    owlready2.JAVA_EXE = java
    version_str = get_java_version(java)
    print(f"[INFO] Java path     : {java}")
    print(f"[INFO] Version Java  : {version_str}")

    mem_mb = get_java_malloc()
    if mem_mb is not None:
        import owlready2.reasoning as _r
        _r.JAVA_MEMORY = mem_mb
        print(f"[INFO] Heap Java     : -Xmx{mem_mb}M")

    return True


# ---------------------------------------------------------------------------
# Chargement de l'ontologie et extraction du domaine DNA repair
# ---------------------------------------------------------------------------


def go_id_to_iri(go_id: str) -> str:
    return GO_NS + go_id.replace(":", "_")


def get_descendants(onto, root_go_id: str) -> set:
    """Retourne les IRI de toutes les classes descendantes de root_go_id
    (racine incluse) par parcours BFS sur subclasses().
    """
    root_iri = go_id_to_iri(root_go_id)
    root_cls = onto.search_one(iri=root_iri)
    if root_cls is None:
        print(f"  [WARN] Classe racine {root_go_id} introuvable dans l'ontologie.")
        return set()

    visited: set = set()
    stack = [root_cls]
    while stack:
        cls = stack.pop()
        if cls.iri in visited:
            continue
        visited.add(cls.iri)
        for sub in cls.subclasses():
            if sub.iri not in visited:
                stack.append(sub)
    return visited


# ---------------------------------------------------------------------------
# Raisonnement
# ---------------------------------------------------------------------------


def run_reasoner(
    onto,
    reasoner_name: str,
    world: World,
    dna_repair_iris: set,
    memory_mb: Optional[int] = None,
) -> Dict[str, Any]:
    """Lance un raisonneur sur l'ontologie et retourne les résultats."""
    result: Dict[str, Any] = {
        "reasoner": reasoner_name,
        "elapsed_seconds": None,
        "ontology_consistent": None,
        "inconsistent_classes_total": [],
        "inconsistent_classes_dna_repair": [],
        "error": None,
    }

    import owlready2.reasoning as _r
    if memory_mb is not None:
        _r.JAVA_MEMORY = memory_mb

    start = time.perf_counter()
    try:
        if reasoner_name == "HermiT":
            owlready2.sync_reasoner(
                [onto],
                infer_property_values=False,
            )
        else:
            raise ValueError(f"Raisonneur inconnu : {reasoner_name}")

        result["ontology_consistent"] = True

    except OwlReadyInconsistentOntologyError as exc:
        result["ontology_consistent"] = False
        result["error"] = str(exc)

    except Exception as exc:
        result["ontology_consistent"] = None
        result["error"] = str(exc)

    finally:
        result["elapsed_seconds"] = round(time.perf_counter() - start, 2)

    try:
        inc_classes: List = list(world.inconsistent_classes())
        result["inconsistent_classes_total"] = [c.iri for c in inc_classes]
        result["inconsistent_classes_dna_repair"] = [
            c.iri for c in inc_classes if c.iri in dna_repair_iris
        ]
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Analyse complète d'une version GO
# ---------------------------------------------------------------------------


def analyse_version(label: str, owl_path: Path) -> Dict[str, Any]:
    """Charge l'ontologie puis lance HermiT sur celle-ci."""
    print(f"\n{'=' * 64}")
    print(f"  Version : {label}")
    print(f"  Fichier : {owl_path}")
    print(f"{'=' * 64}")

    world = World()
    onto = world.get_ontology(str(owl_path)).load()

    nb_classes = len(list(onto.classes()))
    print(f"  Classes chargees  : {nb_classes:,}")

    dna_repair_iris = get_descendants(onto, DOMAIN_ROOT_ID)
    print(f"  Classes DNA repair: {len(dna_repair_iris):,}")

    mem_mb = get_java_malloc()

    reasoner_results: List[Dict] = []
    for rname in REASONERS:
        print(f"\n  -> Lancement du raisonneur {rname}...")

        r = run_reasoner(onto, rname, world, dna_repair_iris, memory_mb=mem_mb)

        print(f"    Temps              : {r['elapsed_seconds']} s")
        print(f"    Ontologie coherente: {r['ontology_consistent']}")
        if r["error"]:
            print(f"    Erreur             : {r['error'][:200]}")
        print(f"    Inc. totales       : {len(r['inconsistent_classes_total'])}")
        print(f"    Inc. DNA repair    : {len(r['inconsistent_classes_dna_repair'])}")

        reasoner_results.append(r)

    return {
        "label": label,
        "owl_path": str(owl_path),
        "nb_classes_total": nb_classes,
        "nb_classes_dna_repair": len(dna_repair_iris),
        "reasoners": reasoner_results,
    }

# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def main() -> None:
    print("=" * 64)
    print("  Analyse des raisonneurs OWL - Gene Ontology")
    print(f"  Domaine : {DOMAIN_LABEL} ({DOMAIN_ROOT_ID})")
    print("=" * 64)

    if not setup_java():
        sys.exit(1)

    versions = [
        ("GO_10-25 (octobre 2025)", PATH_GO_OLD),
        ("GO_01-26 (janvier 2026)", PATH_GO_NEW),
    ]

    all_results: Dict[str, Any] = {"versions": []}

    for label, owl_path in versions:
        if not owl_path.exists():
            print(f"\n[WARN] Fichier OWL introuvable, version ignoree : {owl_path}")
            continue
        version_result = analyse_version(label, owl_path)
        all_results["versions"].append(version_result)

    if not all_results["versions"]:
        print("\n[ERREUR] Aucune ontologie chargee. Verifiez le dossier data/.")
        sys.exit(1)

    print("\n" + "=" * 64)
    print("  Resume comparatif")
    print("=" * 64)
    header = f"  {'Version':<32} {'Raisonneur':<10} {'Temps (s)':>9}  {'Coherente':<12} {'Inc.':<6}"
    print(header)
    print("  " + "-" * 62)
    for version in all_results["versions"]:
        for r in version["reasoners"]:
            consistent_str = str(r["ontology_consistent"])
            print(
                f"  {version['label']:<32} {r['reasoner']:<10} "
                f"{r['elapsed_seconds']:>9.2f}  {consistent_str:<12} "
                f"{len(r['inconsistent_classes_total']):<6}"
            )


if __name__ == "__main__":
    main()
