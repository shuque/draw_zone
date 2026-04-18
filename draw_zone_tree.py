#!/usr/bin/env python3

"""
Draw a DNS zone tree diagram from a zone file using Graphviz.

Usage: python draw_zone_tree.py <zonefile> <origin> [output_name]
Example: python draw_zone_tree.py zonefile.dnskensa.small.txt dnskensa.com dns_tree
"""

import sys
from collections import defaultdict
from graphviz import Digraph

STYLES = {
    "apex": {
        "shape": "box",
        "style": "filled,bold",
        "fillcolor": "#4A90D9",
        "fontcolor": "white",
        "fontname": "Helvetica-Bold",
    },
    "normal": {
        "shape": "box",
        "style": "filled",
        "fillcolor": "#E8F4FD",
        "fontname": "Helvetica",
    },
    "ent": {
        "shape": "box",
        "style": "dashed,filled",
        "fillcolor": "#FFF3CD",
        "fontname": "Helvetica-Oblique",
    },
    "wildcard": {
        "shape": "box",
        "style": "filled",
        "fillcolor": "#F8D7DA",
        "fontname": "Helvetica-Bold",
    },
    "delegation": {
        "shape": "box",
        "style": "filled,bold",
        "fillcolor": "#D4EDDA",
        "fontname": "Helvetica-Bold",
    },
    "glue": {
        "shape": "box",
        "style": "dotted,filled",
        "fillcolor": "#E2E3E5",
        "fontname": "Helvetica",
    },
}

LEGEND_LABELS = [
    ("apex", "Zone Apex"),
    ("normal", "Normal Node"),
    ("ent", "Empty Non-Terminal"),
    ("wildcard", "Wildcard"),
    ("delegation", "Delegation Point"),
    ("glue", "Glue Record"),
]


def parse_zonefile(filename):
    """Parse zone file, return dict of owner_name -> set of RR types."""
    rrsets = defaultdict(set)
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(";"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            owner = parts[0].lower().rstrip(".")
            try:
                idx = parts.index("IN")
                rrtype = parts[idx + 1]
                rrsets[owner].add(rrtype)
            except (ValueError, IndexError):
                continue
    return rrsets


def build_tree(rrsets, origin):
    """Build tree nodes from owner names, creating intermediate ENT nodes."""
    nodes = {}

    def ensure_node(name):
        if name not in nodes:
            nodes[name] = {"rrtypes": set(), "children": set()}

    ensure_node(origin)

    for owner, rrtypes in rrsets.items():
        ensure_node(owner)
        nodes[owner]["rrtypes"] = rrtypes

        current = owner
        while current != origin:
            parts = current.split(".", 1)
            if len(parts) < 2:
                break
            parent = parts[1]
            ensure_node(parent)
            nodes[parent]["children"].add(current)
            current = parent

    return nodes


def find_delegation_points(nodes, origin):
    """Return set of names that are delegation points (NS but not apex)."""
    return {
        name
        for name, info in nodes.items()
        if "NS" in info["rrtypes"] and name != origin
    }


def classify_node(name, nodes, origin, delegation_points):
    """Classify a node for visual styling."""
    if name == origin:
        return "apex"

    label = name.split(".")[0]
    if label == "*":
        return "wildcard"

    if name in delegation_points:
        return "delegation"

    for dp in delegation_points:
        if name.endswith("." + dp):
            return "glue"

    if not nodes[name]["rrtypes"]:
        return "ent"

    return "normal"


def make_node_label(name, rrtypes, origin):
    """Build the display label for a node: short name + RR type list."""
    short = name if name == origin else name.split(".")[0]
    if rrtypes:
        type_str = ", ".join(sorted(rrtypes))
        return f"{short}\n{{{type_str}}}"
    return f"{short}\n(ENT)"


def add_legend(dot):
    """Add a legend subgraph explaining node styles."""
    with dot.subgraph(name="cluster_legend") as lg:
        lg.attr(
            label="Legend",
            style="rounded",
            color="#999999",
            fontname="Helvetica-Bold",
        )
        lg.attr("node", shape="box", fontsize="9", width="1.4")
        keys = []
        for key, desc in LEGEND_LABELS:
            node_id = f"legend_{key}"
            lg.node(node_id, label=desc, **STYLES[key])
            keys.append(node_id)
        for i in range(len(keys) - 1):
            lg.edge(keys[i], keys[i + 1], style="invis")


def draw_tree(zonefile, origin, output="dns_tree"):
    origin = origin.lower().rstrip(".")
    rrsets = parse_zonefile(zonefile)
    nodes = build_tree(rrsets, origin)
    delegation_points = find_delegation_points(nodes, origin)

    dot = Digraph("dns_tree", format="png")
    dot.attr(rankdir="TB", splines="line", nodesep="0.5", ranksep="0.8")
    dot.attr("node", fontsize="11")
    dot.attr("edge", color="#666666", arrowsize="0.6")
    dot.attr(
        label=f"DNS Zone Tree:  {origin}",
        labelloc="t",
        fontsize="18",
        fontname="Helvetica-Bold",
    )

    for name in sorted(nodes):
        node_type = classify_node(name, nodes, origin, delegation_points)
        label = make_node_label(name, nodes[name]["rrtypes"], origin)
        dot.node(name, label=label, **STYLES[node_type])

    for name, info in nodes.items():
        for child in sorted(info["children"]):
            dot.edge(name, child, tailport="s", headport="n")

    add_legend(dot)

    dot.render(output, cleanup=True)
    print(f"Tree diagram written to {output}.png")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <zonefile> <origin> [output_name]")
        sys.exit(1)
    draw_tree(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "dns_tree")
