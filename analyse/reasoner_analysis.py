#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 4 : Utilisation d'un raisonneur OWL (HermiT, Pellet).

Lance HermiT puis Pellet sur les deux versions de Gene Ontology
(octobre 2025 et janvier 2026), domaine DNA repair (GO:0006281).

Sorties
-------
- Console : tableau comparatif (temps, incohérences).
- result/reasoner/reasoner_report.json  : données brutes.
- result/reasoner/reasoner_report.md    : rapport lisible.

Prérequis
---------
- Java installé et accessible (détection automatique via PATH).
- Si Java n'est pas trouvé, configurer son chemin dans reasoner_config.ini
  (même dossier que ce script).
- HermiT : Java 11+
- Pellet : Java 25+ (JAR Jena bundlé dans owlready2 compilé pour Java 25)
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

REASONERS = ["HermiT", "Pellet"]

# ---------------------------------------------------------------------------
# Vérification et configuration de Java
# ---------------------------------------------------------------------------


def find_java() -> Optional[str]:
    """Cherche java dans le PATH système, puis dans reasoner_config.ini."""
    java = shutil.which("java")
    if java:
        return java

    return None


def get_java_version(java_exe: str) -> Tuple[int, str]:
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
            return int(match.group(1)), first_line
        match = re.search(r'"(\d+)"', first_line)
        if match:
            return int(match.group(1)), first_line
        return 0, first_line
    except Exception as exc:
        return 0, str(exc)


def get_java_malloc() -> Optional[int]:
    """Définit la taille de la mémoire JVM reasoner_config.ini si défini."""
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
    """Configure owlready2.JAVA_EXE. Vérifie la version Java."""
    java = find_java()
    if not java:
        print("=" * 64)
        print("  ERREUR : Java introuvable sur ce système.")
        print()
        print("  HermiT et Pellet sont des raisonneurs écrits en Java.")
        print("  Solutions :")
        print("    1. Installez Java (JRE/JDK >= 11) et ajoutez-le au PATH.")
        print(f"    2. Ou renseignez son chemin dans : {CONFIG_PATH}")
        print()
        print("  Exemple de contenu pour reasoner_config.ini (Windows) :")
        print("    [java]")
        print("    exe = C:\\Program Files\\Java\\jdk-21\\bin\\java.exe")
        print()
        print("  Exemple (Linux) :")
        print("    [java]")
        print("    exe = /usr/lib/jvm/java-21-openjdk-amd64/bin/java")
        print("=" * 64)
        return False

    owlready2.JAVA_EXE = java
    major, version_str = get_java_version(java)
    print(f"[INFO] Java detecte : {java}")
    print(f"[INFO] Version Java  : {version_str}  (majeure={major})")

    mem_mb = get_java_malloc()
    if mem_mb is not None:
        try:
            owlready2.reasoning.JAVA_MEMORY = mem_mb
            print(f"[INFO] Heap Java (owlready2) : -Xmx{mem_mb}M")
        except Exception as exc:
            print(f"[WARN] Impossible de configurer owlready2.reasoning.JAVA_MEMORY: {exc}")

    if 0 < major < 25:
        print()
        print("  +-- AVERTISSEMENT -- Compatibilite Pellet ----------------")
        print(f"  |  Java {major} detecte, mais le JAR Pellet bundle dans")
        print("  |  owlready2 requiert Java 25+ (class file version 69.0).")
        print("  |")
        print("  |  -> HermiT fonctionnera normalement.")
        print("  |  -> Pellet echouera avec UnsupportedClassVersionError.")
        print("  |")
        print("  |  Pour utiliser Pellet, installez Java 25 (ou +) :")
        print("  |    Windows : https://adoptium.net/ (Temurin 25)")
        print("  |    Ubuntu  : sudo apt install openjdk-25-jre-headless")
        print("  +----------------------------------------------------------")
        print()

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


def run_reasoner(onto, reasoner_name: str, world: World, dna_repair_iris: set) -> Dict[str, Any]:
    """Lance un raisonneur sur l'ontologie et retourne les résultats."""
    result: Dict[str, Any] = {
        "reasoner": reasoner_name,
        "elapsed_seconds": None,
        "ontology_consistent": None,
        "inconsistent_classes_total": [],
        "inconsistent_classes_dna_repair": [],
        "error": None,
    }

    start = time.perf_counter()
    try:
        if reasoner_name == "HermiT":
            owlready2.sync_reasoner(
                [onto],
                infer_property_values=False,
            )
        elif reasoner_name == "Pellet":
            owlready2.sync_reasoner_pellet(
                [onto],
                infer_property_values=False,
                infer_data_property_values=False,
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
    """Charge l'ontologie puis lance HermiT et Pellet sur celle-ci."""
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

    reasoner_results: List[Dict] = []
    for rname in REASONERS:
        print(f"\n  -> Lancement du raisonneur {rname}...")

        r = run_reasoner(onto, rname, world, dna_repair_iris)

        elapsed = r["elapsed_seconds"]
        consistent = r["ontology_consistent"]
        nb_inc = len(r["inconsistent_classes_total"])
        nb_inc_dna = len(r["inconsistent_classes_dna_repair"])

        print(f"    Temps              : {elapsed} s")
        print(f"    Ontologie coherente: {consistent}")
        if r["error"]:
            print(f"    Erreur             : {r['error'][:200]}")
        print(f"    Inc. totales       : {nb_inc}")
        print(f"    Inc. DNA repair    : {nb_inc_dna}")

        reasoner_results.append(r)

    return {
        "label": label,
        "owl_path": str(owl_path),
        "nb_classes_total": nb_classes,
        "nb_classes_dna_repair": len(dna_repair_iris),
        "reasoners": reasoner_results,
    }


# ---------------------------------------------------------------------------
# Export des résultats
# ---------------------------------------------------------------------------


def export_json(data: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] JSON exporte : {path}")


def export_markdown(data: Dict, path: Path) -> None:
    lines: List[str] = []
    lines.append("# Analyse des raisonneurs OWL - Gene Ontology\n\n")
    lines.append(f"**Domaine :** {DOMAIN_LABEL} (`{DOMAIN_ROOT_ID}`)  \n")
    lines.append(f"**Raisonneurs :** {', '.join(REASONERS)}  \n\n")
    lines.append("---\n\n")

    for version in data["versions"]:
        lines.append(f"## Version : {version['label']}\n\n")
        lines.append(f"- Fichier OWL : `{Path(version['owl_path']).name}`\n")
        lines.append(f"- Classes totales : {version['nb_classes_total']:,}\n")
        lines.append(f"- Classes DNA repair : {version['nb_classes_dna_repair']:,}\n\n")

        lines.append(
            "| Raisonneur | Temps (s) | Coherente | Inc. totales | Inc. DNA repair |\n"
        )
        lines.append("|---|---|---|---|---|\n")
        for r in version["reasoners"]:
            if r["ontology_consistent"] is True:
                sym = "oui"
            elif r["ontology_consistent"] is False:
                sym = "non"
            else:
                sym = "N/A"

            err_note = ""
            if r["error"]:
                snippet = r["error"][:60] + ("..." if len(r["error"]) > 60 else "")
                err_note = f" (erreur: `{snippet}`)"

            lines.append(
                f"| {r['reasoner']} "
                f"| {r['elapsed_seconds']} "
                f"| {sym}{err_note} "
                f"| {len(r['inconsistent_classes_total'])} "
                f"| {len(r['inconsistent_classes_dna_repair'])} |\n"
            )

        for r in version["reasoners"]:
            if r["inconsistent_classes_dna_repair"]:
                lines.append(
                    f"\n### Classes incoherentes - {r['reasoner']} - DNA repair\n\n"
                )
                for iri in sorted(r["inconsistent_classes_dna_repair"]):
                    go_id = iri.split("/")[-1].replace("_", ":")
                    lines.append(f"- `{go_id}` - {iri}\n")
                lines.append("\n")

        lines.append("\n")

    lines.append("---\n\n")
    lines.append("*Rapport genere automatiquement par `reasoner_analysis.py`.*\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")
    print(f"[OK] Markdown exporte : {path}")


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

    export_json(all_results, RESULTS_DIR / "reasoner_report.json")
    export_markdown(all_results, RESULTS_DIR / "reasoner_report.md")

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
