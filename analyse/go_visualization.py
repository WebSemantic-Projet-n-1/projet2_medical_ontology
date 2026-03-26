#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partie 1 - Script 5 : Visualisation interactive de l'ontologie GO.
Utilisé uniquement dans le notebook analyse.ipynb
Génère le fichier HTML de la visualisation interactive.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from pyvis.network import Network

from load_ontologies import GO_NS


DOMAIN_INFO: Mapping[str, Mapping[str, str]] = {
    "GO:0006281": {"label": "DNA repair", "color": "#f05e56"},
    "GO:0006629": {"label": "Lipid metabolism", "color": "#4575b4"},
    "GO:0012501": {"label": "Apoptosis", "color": "#1a9850"},
}
OVERLAP_COLOR = "#7b3294"
CONTEXT_COLOR = "#bdbdbd"
ROOT_GO_ID = "GO:0008150"
LAYOUT_RANDOM_SEED = 42


def go_id_to_iri(go_id: str) -> str:
    return GO_NS + go_id.replace(":", "_")


def iri_to_go_id(iri: str) -> str:
    local = iri.rsplit("/", 1)[-1]
    return local.replace("_", ":", 1) if local.startswith("GO_") else local


def normalize_iri(node) -> str:
    iri = getattr(node, "iri", None)
    if iri:
        return str(iri)

    raw = str(node)
    if raw.startswith("obo."):
        return GO_NS + raw.split(".", 1)[1]
    return raw


def get_descendants(onto, root_go_id: str) -> Set[str]:
    """Return the transitive `is_a` descendants of a GO term, root included."""
    root_iri = go_id_to_iri(root_go_id)
    query = (
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
        "SELECT DISTINCT ?sub WHERE { "
        "?sub rdfs:subClassOf* <%s> . "
        "FILTER(ISIRI(?sub)) }"
    ) % root_iri
    rows = list(onto.world.sparql(query))
    return {normalize_iri(row[0]) for row in rows}


def build_class_index(onto) -> Dict[str, object]:
    return {cls.iri: cls for cls in onto.classes() if getattr(cls, "iri", None)}


def get_named_parent_iris(cls) -> Set[str]:
    return {parent.iri for parent in cls.is_a if getattr(parent, "iri", None)}


def get_label(index: Mapping[str, object], iri: str) -> str:
    cls = index.get(iri)
    if cls is None:
        return iri_to_go_id(iri)
    label = getattr(cls, "label", None)
    if isinstance(label, list) and label:
        return str(label[0])
    if label:
        return str(label)
    return iri_to_go_id(iri)


def compute_scope_summary(onto, domain_roots: Sequence[str]) -> Dict[str, object]:
    index = build_class_index(onto)
    domain_sets = {root: get_descendants(onto, root) for root in domain_roots}
    total = set(index.keys())
    union = set().union(*domain_sets.values()) if domain_sets else set()
    outside = total - union

    memberships: Dict[str, Tuple[str, ...]] = {}
    for iri in union:
        memberships[iri] = tuple(sorted(root for root, members in domain_sets.items() if iri in members))

    overlap_rows = []
    for membership_size in range(1, len(domain_roots) + 1):
        overlap_rows.append(
            {
                "nb_domaines_couverts": membership_size,
                "nb_classes": sum(1 for membership in memberships.values() if len(membership) == membership_size),
            }
        )

    return {
        "index": index,
        "domain_sets": domain_sets,
        "total": total,
        "union": union,
        "outside": outside,
        "memberships": memberships,
        "overlap_df": pd.DataFrame(overlap_rows),
    }


def _parent_map(index: Mapping[str, object], iris: Iterable[str]) -> Dict[str, Set[str]]:
    iris = set(iris)
    parent_map: Dict[str, Set[str]] = {}
    for iri in iris:
        cls = index.get(iri)
        if cls is None:
            continue
        parent_map[iri] = {parent for parent in get_named_parent_iris(cls) if parent in index}
    return parent_map


def build_status_map(onto_old, onto_new, domain_roots: Sequence[str]) -> Dict[str, str]:
    old_scope = compute_scope_summary(onto_old, domain_roots)
    new_scope = compute_scope_summary(onto_new, domain_roots)

    current_union = new_scope["union"]
    old_index = old_scope["index"]
    new_index = new_scope["index"]

    old_parents = _parent_map(old_index, current_union)
    new_parents = _parent_map(new_index, current_union)

    status_map: Dict[str, str] = {}
    for iri in current_union:
        if iri not in old_index:
            status_map[iri] = "new"
        elif old_parents.get(iri, set()) != new_parents.get(iri, set()):
            status_map[iri] = "hierarchy_changed"
        else:
            status_map[iri] = "stable"
    return status_map


def make_macro_summary(onto_old, onto_new, domain_roots: Sequence[str]) -> Dict[str, object]:
    old_scope = compute_scope_summary(onto_old, domain_roots)
    new_scope = compute_scope_summary(onto_new, domain_roots)

    df_scope = pd.DataFrame(
        {
            "classes_total": [len(old_scope["total"]), len(new_scope["total"])],
            "classes_exploitables": [len(old_scope["union"]), len(new_scope["union"])],
            "classes_hors_portee": [len(old_scope["outside"]), len(new_scope["outside"])],
        },
        index=["GO_10-25", "GO_01-26"],
    )
    df_scope["pct_exploitables"] = (
        (df_scope["classes_exploitables"] / df_scope["classes_total"]) * 100
    ).round(2)

    domain_rows: List[Dict[str, object]] = []
    for version, scope in (("GO_10-25", old_scope), ("GO_01-26", new_scope)):
        for root in domain_roots:
            domain_rows.append(
                {
                    "version": version,
                    "go_id": root,
                    "domaine": DOMAIN_INFO.get(root, {}).get("label", root),
                    "nb_classes": len(scope["domain_sets"][root]),
                }
            )
    df_domains = pd.DataFrame(domain_rows)

    overlap_new = new_scope["overlap_df"].copy()
    overlap_new["description"] = overlap_new["nb_domaines_couverts"].map(
        {
            1: "Dans 1 sous-domaine étudié",
            2: "Dans 2 sous-domaines étudiés",
            3: "Dans les 3 sous-domaines étudiés",
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    ax_scope = axes[0]
    ax_scope.pie(
        [
            df_scope.loc["GO_01-26", "classes_exploitables"],
            df_scope.loc["GO_01-26", "classes_hors_portee"],
        ],
        radius=1.0,
        startangle=90,
        counterclock=False,
        colors=["#4c78a8", "#d9d9d9"],
        wedgeprops={"width": 0.28, "edgecolor": "white"},
    )
    ax_scope.pie(
        [
            df_scope.loc["GO_10-25", "classes_exploitables"],
            df_scope.loc["GO_10-25", "classes_hors_portee"],
        ],
        radius=0.68,
        startangle=90,
        counterclock=False,
        colors=["#4c78a8", "#d9d9d9"],
        wedgeprops={"width": 0.28, "edgecolor": "white"},
    )
    ax_scope.set_title("Vue macro - couverture globale de GO")
    ax_scope.text(
        0,
        0.08,
        f"Ext. GO_01-26\n{df_scope.loc['GO_01-26', 'pct_exploitables']}%",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )
    ax_scope.text(
        0,
        -0.24,
        f"Int. GO_10-25\n{df_scope.loc['GO_10-25', 'pct_exploitables']}%",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
    )
    ax_scope.legend(
        ["Exploitables par l'extension", "Hors portee"],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=2,
        frameon=False,
    )
    ax_scope.set(aspect="equal")

    ax_domains = axes[1]
    pivot = df_domains.pivot(index="domaine", columns="version", values="nb_classes")
    colors = ["#8da0cb", "#fc8d62"]
    pivot.plot(kind="bar", ax=ax_domains, color=colors, width=0.75)
    ax_domains.set_title("Vue macro - taille des 3 sous-domaines")
    ax_domains.set_ylabel("Nombre de classes")
    ax_domains.set_xlabel("")
    ax_domains.legend(frameon=False, title="Version")
    ax_domains.tick_params(axis="x", rotation=20)

    plt.tight_layout()

    return {
        "old_scope": old_scope,
        "new_scope": new_scope,
        "df_scope": df_scope,
        "df_domains": df_domains,
        "df_overlap_new": overlap_new[["description", "nb_classes"]],
        "figure": fig,
    }


def _border_style(status: str) -> Tuple[str, float]:
    if status == "new":
        return "#fdb863", 2.8
    if status == "hierarchy_changed":
        return "#e66101", 2.4
    return "rgba(0,0,0,0)", 0.0


def _collect_ancestor_context(index: Mapping[str, object], start_iris: Iterable[str], stop_iri: str | None) -> Set[str]:
    context: Set[str] = set()
    queue = deque(start_iris)
    visited: Set[str] = set()

    while queue:
        iri = queue.popleft()
        if iri in visited:
            continue
        visited.add(iri)
        cls = index.get(iri)
        if cls is None:
            continue
        for parent in get_named_parent_iris(cls):
            if parent not in index:
                continue
            context.add(parent)
            if stop_iri is None or parent != stop_iri:
                queue.append(parent)
    return context


def _domain_memberships(scope_summary: Mapping[str, object], iri: str) -> Tuple[str, ...]:
    memberships = scope_summary["memberships"]
    return memberships.get(iri, ())


def _fill_color(domain_roots: Tuple[str, ...]) -> str:
    if not domain_roots:
        return CONTEXT_COLOR
    if len(domain_roots) > 1:
        return OVERLAP_COLOR
    return DOMAIN_INFO.get(domain_roots[0], {}).get("color", "#4c78a8")


def _build_network_graph(
    index: Mapping[str, object],
    included: Set[str],
) -> nx.DiGraph:
    graph = nx.DiGraph()
    for iri in included:
        graph.add_node(iri)

    for iri in included:
        cls = index.get(iri)
        if cls is None:
            continue
        for parent in get_named_parent_iris(cls):
            if parent in included:
                graph.add_edge(parent, iri)
    return graph


def _shape_and_size(
    iri: str,
    root_iri: str,
    studied_root_iris: Set[str],
    exploitable: bool,
) -> Tuple[str, int]:
    if iri == root_iri:
        return "diamond", 36
    if iri in studied_root_iris:
        return "star", 33
    return "dot", 18 if exploitable else 12


def _tooltip_lines(
    go_id: str,
    label: str,
    memberships: Tuple[str, ...],
    exploitable: bool,
    status: str,
) -> List[str]:
    lines = [
        go_id,
        label,
        f"Exploitable: {'oui' if exploitable else 'non'}",
        f"Statut: {status}",
    ]
    domain_labels = [DOMAIN_INFO[root]["label"] for root in memberships if root in DOMAIN_INFO]
    if domain_labels:
        lines.append("Sous-domaines: " + ", ".join(domain_labels))
    return lines


def _add_network_nodes(
    net: Network,
    graph: nx.DiGraph,
    index: Mapping[str, object],
    scope_summary: Mapping[str, object],
    status_map: Mapping[str, str],
    root_iri: str,
    studied_root_iris: Set[str],
) -> None:
    union = scope_summary["union"]
    for iri in sorted(graph.nodes):
        go_id = iri_to_go_id(iri)
        label = get_label(index, iri)
        memberships = _domain_memberships(scope_summary, iri)
        fill_color = _fill_color(memberships)
        status = status_map.get(iri, "context")
        border_color, border_width = _border_style(status)
        exploitable = iri in union
        is_root = iri in studied_root_iris or iri == root_iri
        shape, size = _shape_and_size(iri, root_iri, studied_root_iris, exploitable)

        net.add_node(
            iri,
            label=go_id,
            title="\n".join(_tooltip_lines(go_id, label, memberships, exploitable, status)),
            color={
                "background": fill_color,
                "border": border_color,
                "highlight": {"background": fill_color, "border": border_color},
            },
            borderWidth=border_width,
            shape=shape,
            size=size,
            font={"size": 13 if is_root else 10},
        )


def _legend_html() -> str:
    return """
<style>
#go-legend {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  background: rgba(255, 255, 255, 0.97);
  border: 1px solid #d7d7d7;
  border-radius: 12px;
  padding: 12px 14px;
  width: 320px;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 13px;
  color: #1f1f1f;
}
#go-legend h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}
#go-legend .group-title {
  margin: 10px 0 6px 0;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #505050;
}
#go-legend .item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0;
}
#go-legend .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 1px solid #cfcfcf;
  flex: 0 0 12px;
}
#go-legend .ring {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ffffff;
  flex: 0 0 12px;
}
</style>
<div id="go-legend">
  <h3><b>Légende</b></h3>
  <div class="group-title">Sous-domaines</div>
  <div class="item"><span class="dot" style="background:#d73027"></span>DNA repair</div>
  <div class="item"><span class="dot" style="background:#4575b4"></span>Lipid metabolism</div>
  <div class="item"><span class="dot" style="background:#1a9850"></span>Apoptosis</div>
  <div class="item"><span class="dot" style="background:#7b3294"></span>Chevauchement entre sous-domaines</div>
  <div class="item"><span class="dot" style="background:#bdbdbd"></span>Contexte hors portée directe</div>

  <div class="group-title">Statut</div>
  <div class="item"><span class="ring" style="border:3px solid #fdb863"></span>Nouveau terme (jan. 2026)</div>
  <div class="item"><span class="ring" style="border:3px solid #e66101"></span>Hiérarchie modifiée</div>
  <div class="item"><span class="ring" style="border:1px solid #cfcfcf"></span>Stable / contexte</div>

  <div class="group-title">Forme</div>
  <div class="item">◆ Racine biologique_process (`GO:0008150`)</div>
  <div class="item">★ Racines des sous-domaines étudies</div>
</div>
"""


def _inject_legend(output_path: Path) -> None:
    html = output_path.read_text(encoding="utf-8")
    if ".vis-tooltip { white-space: pre-line;" not in html and "</style>" in html:
        html = html.replace(
            "</style>",
            "\n.vis-tooltip { white-space: pre-line; max-width: 520px; }\n</style>",
            1,
        )
    legend = _legend_html()
    if "id=\"go-legend\"" in html:
        output_path.write_text(html, encoding="utf-8")
        return
    if "</body>" in html:
        html = html.replace("</body>", f"{legend}\n</body>")
    else:
        html += legend
    output_path.write_text(html, encoding="utf-8")


def build_interactive_network(
    onto_old,
    onto_new,
    domain_roots: Sequence[str],
    output_path: str | Path,
    root_go_id: str = ROOT_GO_ID,
) -> Path:
    new_scope = compute_scope_summary(onto_new, domain_roots)
    status_map = build_status_map(onto_old, onto_new, domain_roots)

    index_new = new_scope["index"]
    root_iri = go_id_to_iri(root_go_id)
    studied_root_iris = {go_id_to_iri(go_id) for go_id in domain_roots}
    context_iris = _collect_ancestor_context(index_new, studied_root_iris, stop_iri=root_iri)
    included = set(new_scope["union"]) | context_iris | studied_root_iris
    if root_iri in index_new:
        included.add(root_iri)

    graph = _build_network_graph(index_new, included)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    net = Network(height="780px", width="100%", directed=True, bgcolor="#ffffff", font_color="#202020")
    net.barnes_hut(gravity=-2500, central_gravity=0.18, spring_length=140, spring_strength=0.02, damping=0.92)

    _add_network_nodes(net, graph, index_new, new_scope, status_map, root_iri, studied_root_iris)

    for src, dst in graph.edges:
        net.add_edge(src, dst, arrows="to", color="#c7c7c7")

    net.set_options(
        """
        const options = {
          "layout": {
            "improvedLayout": true,
            "randomSeed": %d
          },
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true
          },
          "physics": {
            "minVelocity": 0.75
          }
        }
        """
        % LAYOUT_RANDOM_SEED
    )
    net.write_html(str(output_path), notebook=False)
    _inject_legend(output_path)
    return output_path
