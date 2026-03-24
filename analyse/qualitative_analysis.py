#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 3 : Analyse qualitative sur 5 termes du domaine (DNA repair).

STRUCTURE DU SCRIPT
-------------------
1. Charger les deux versions de GO via load_ontologies.
2. Pour chacun des 5 termes GO sélectionnés :
   - Comparer la définition (IAO:0000115 ou rdfs:comment).
   - Comparer la position dans la hiérarchie (parents directs is_a).
   - Identifier les changements dans les relations OBO (part_of, regulates…).
3. Sortie : rapport Markdown.
"""

from typing import Any, Dict, List, Optional
from load_ontologies import GO_NS, PATH_GO_NEW, PATH_GO_OLD, load_ontology
from owlready2 import Restriction

# ---------------------------------------------------------------------------
# 5 termes du domaine DNA repair (GO:0006281) et ses sous-processus majeurs
# ---------------------------------------------------------------------------
TERM_IDS: List[str] = [
    "GO:0006281",  # DNA repair (racine du domaine)
    "GO:0006284",  # base-excision repair
    "GO:0006289",  # nucleotide-excision repair
    "GO:0006298",  # mismatch repair
    "GO:0006302",  # double-strand break repair
]

# Noms lisibles des relations OBO les plus courantes dans GO
OBO_RELATION_LABELS: Dict[str, str] = {
    "BFO_0000050": "part_of",
    "BFO_0000051": "has_part",
    "RO_0002211":  "regulates",
    "RO_0002212":  "negatively_regulates",
    "RO_0002213":  "positively_regulates",
    "RO_0002264":  "acts_upstream_of_or_within",
    "RO_0002295":  "results_in_development_of",
    "RO_0002296":  "results_in_morphogenesis_of",
    "RO_0002297":  "results_in_maturation_of",
    "RO_0001000":  "derives_from",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def go_id_to_iri(go_id: str) -> str:
    return GO_NS + go_id.replace(":", "_")


def iri_to_go_id(iri: str) -> str:
    """http://purl.obolibrary.org/obo/GO_0006281 → GO:0006281"""
    local = iri.rsplit("/", 1)[-1]
    return local.replace("_", ":", 1) if local.startswith("GO_") else local


def _prop_label(prop) -> str:
    """Retourne un label lisible pour une propriété OBO."""
    local = prop.iri.rsplit("/", 1)[-1] if hasattr(prop, "iri") else str(prop)
    return OBO_RELATION_LABELS.get(local, local)


def get_cls(onto, go_id: str):
    """Recherche et retourne la classe OWL correspondant à go_id, ou None."""
    return onto.search_one(iri=go_id_to_iri(go_id))


# ---------------------------------------------------------------------------
# Fonctions d'extraction
# ---------------------------------------------------------------------------

def get_definition(onto, go_id: str) -> Optional[str]:
    """Retourne la définition du terme (IAO:0000115) ou rdfs:comment, sinon None."""
    cls = get_cls(onto, go_id)
    if cls is None:
        return None

    # Définition OBO officielle (IAO:0000115)
    iao_def = getattr(cls, "IAO_0000115", None)
    if iao_def:
        value = iao_def[0] if isinstance(iao_def, list) else iao_def
        if value:
            return str(value)

    # Fallback : rdfs:comment
    comment = getattr(cls, "comment", None)
    if comment:
        value = comment[0] if isinstance(comment, list) else comment
        if value:
            return str(value)

    return None


def get_label(onto, go_id: str) -> str:
    """Retourne le label (rdfs:label) ou le go_id si absent."""
    cls = get_cls(onto, go_id)
    if cls is None:
        return go_id
    label = getattr(cls, "label", None)
    if label:
        return label[0] if isinstance(label, list) else str(label)
    return go_id


def get_parents(onto, go_id: str) -> List[str]:
    """Retourne la liste des IRI de parents directs is_a (classes nommées uniquement)."""
    cls = get_cls(onto, go_id)
    if cls is None:
        return []
    return [
        p.iri for p in cls.is_a
        if hasattr(p, "iri") and p.iri
    ]


def get_relations(onto, go_id: str) -> Dict[str, List[str]]:
    """Retourne les relations OBO sous forme {label_relation: [go_id_cible, …]}.

    Dans OWL/OBO, les relations comme part_of et regulates sont encodées
    sous forme de restrictions existentielles (ObjectSomeValuesFrom) dans is_a.
    """
    cls = get_cls(onto, go_id)
    if cls is None:
        return {}

    relations: Dict[str, List[str]] = {}
    for axiom in cls.is_a:
        if not isinstance(axiom, Restriction):
            continue
        prop_label = _prop_label(axiom.property)
        target = axiom.value
        if target is None or not hasattr(target, "iri"):
            continue
        target_id = iri_to_go_id(target.iri)
        relations.setdefault(prop_label, []).append(target_id)

    return relations


# ---------------------------------------------------------------------------
# Comparaison d'un terme entre les deux versions
# ---------------------------------------------------------------------------

def compare_term(onto_old, onto_new, go_id: str) -> Dict[str, Any]:
    """Compare un terme GO entre deux versions de l'ontologie.

    Returns
    -------
    dict avec les clés :
        go_id, label,
        definition_old, definition_new, definition_changed,
        parents_old, parents_new, parents_added, parents_removed,
        relations_old, relations_new, relations_added, relations_removed
    """
    # Récupération des labels dans chaque ontologie. get_label() retourne
    # au minimum l'identifiant (go_id) si le terme est absent.
    label_new = get_label(onto_new, go_id)
    label_old = get_label(onto_old, go_id)

    # Fallback explicite : si le nouveau label n'est qu'un identifiant brut
    # mais que l'ancienne ontologie possède un vrai label, on utilise l'ancien.
    if label_new == go_id and label_old != go_id:
        label = label_old
    else:
        label = label_new

    def_old = get_definition(onto_old, go_id)
    def_new = get_definition(onto_new, go_id)

    parents_old = set(get_parents(onto_old, go_id))
    parents_new = set(get_parents(onto_new, go_id))

    rel_old = get_relations(onto_old, go_id)
    rel_new = get_relations(onto_new, go_id)

    # Relations ajoutées / supprimées : comparaison par (relation, cible)
    pairs_old: set = {(r, t) for r, targets in rel_old.items() for t in targets}
    pairs_new: set = {(r, t) for r, targets in rel_new.items() for t in targets}

    return {
        "go_id":               go_id,
        "label":               label,
        "definition_old":      def_old,
        "definition_new":      def_new,
        "definition_changed":  def_old != def_new,
        "parents_old":         sorted(iri_to_go_id(p) for p in parents_old),
        "parents_new":         sorted(iri_to_go_id(p) for p in parents_new),
        "parents_added":       sorted(iri_to_go_id(p) for p in (parents_new - parents_old)),
        "parents_removed":     sorted(iri_to_go_id(p) for p in (parents_old - parents_new)),
        "relations_old":       rel_old,
        "relations_new":       rel_new,
        "relations_added":     sorted(pairs_new - pairs_old),
        "relations_removed":   sorted(pairs_old - pairs_new),
    }


# ---------------------------------------------------------------------------
# Formatage de la sortie Markdown
# ---------------------------------------------------------------------------

def _fmt_definition(label: str, definition: Optional[str]) -> str:
    if definition is None:
        return f"  *{label}* : (absente)"
    short = definition[:200] + "..." if len(definition) > 200 else definition
    return f"  *{label}* : {short}"


def _section_definition(c: Dict[str, Any]) -> List[str]:
    lines = ["", "### Definition"]
    if not c["definition_changed"]:
        lines.append("  Inchangee entre les deux versions.")
    else:
        lines.append(_fmt_definition("oct. 2025", c["definition_old"]))
        lines.append(_fmt_definition("jan. 2026", c["definition_new"]))
    return lines


def _section_hierarchy(c: Dict[str, Any]) -> List[str]:
    lines = ["", "### Hierarchie (parents is_a)"]
    if not c["parents_added"] and not c["parents_removed"]:
        lines.append("  Aucun changement de hierarchie.")
    else:
        for p in c["parents_added"]:
            lines.append(f"  [+] Ajoute   : {p}")
        for p in c["parents_removed"]:
            lines.append(f"  [-] Retire   : {p}")
    parents_str = ", ".join(c["parents_new"]) or "(aucun)"
    lines.append(f"  Parents (jan. 2026) : {parents_str}")
    return lines


def _section_relations(c: Dict[str, Any]) -> List[str]:
    lines = ["", "### Relations OBO (part_of, regulates...)"]
    if not c["relations_added"] and not c["relations_removed"]:
        lines.append("  Aucun changement de relations.")
    else:
        for rel, tgt in c["relations_added"]:
            lines.append(f"  [+] Ajoutee  : {rel} -> {tgt}")
        for rel, tgt in c["relations_removed"]:
            lines.append(f"  [-] Retiree  : {rel} -> {tgt}")
    if c["relations_new"]:
        lines.append("  Relations actuelles (jan. 2026) :")
        for rel, targets in sorted(c["relations_new"].items()):
            targets_str = ", ".join(targets)
            lines.append(f"    - {rel} : {targets_str}")
    return lines


def format_report(comparisons: List[Dict[str, Any]]) -> str:
    term_list = ", ".join(c["go_id"] for c in comparisons)
    lines: List[str] = [
        "# Analyse qualitative - DNA repair (GO:0006281)",
        "",
        "Versions comparees : GO oct. 2025 -> GO jan. 2026",
        f"Termes analyses : {term_list}",
        "",
    ]

    for c in comparisons:
        lines += [
            "---",
            f"## {c['go_id']} – {c['label']}",
        ]
        lines += _section_definition(c)
        lines += _section_hierarchy(c)
        lines += _section_relations(c)
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def main() -> None:
    """Analyse qualitative des 5 termes DNA repair entre les deux versions GO."""
    print("Chargement de l'ontologie GO oct. 2025 …")
    onto_old = load_ontology(PATH_GO_OLD)

    print("Chargement de l'ontologie GO jan. 2026 …")
    onto_new = load_ontology(PATH_GO_NEW)

    print(f"\nComparaison qualitative de {len(TERM_IDS)} termes …\n")
    comparisons = [compare_term(onto_old, onto_new, gid) for gid in TERM_IDS]

    # Rapport Markdown
    report = format_report(comparisons)
    print(report)

if __name__ == "__main__":
    main()
