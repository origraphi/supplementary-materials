"""Calculate BioFabric edge counts for the Rome graph benchmark datasets."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Edge:
    source: str
    target: str


@dataclass(frozen=True)
class GraphStats:
    """Statistics for one graph after BioFabric ordering."""

    name: str
    node_count: int
    edge_count: int
    uncollapsed_lanes: int
    partially_collapsed_lanes: int
    layered_edges: int
    average_degree: float = 0.0
    maximum_degree: int = 0

    @property
    def lane_savings(self) -> int:
        return self.uncollapsed_lanes - self.partially_collapsed_lanes


def _read_graph(path: Path) -> tuple[list[str], list[Edge]]:
    """Read a D3/networkx node-link graph."""
    with path.open(encoding="utf-8") as graph_file:
        data: dict[str, Any] = json.load(graph_file)

    nodes = [str(node["id"]) for node in data.get("nodes", [])]
    edges = [
        Edge(source=str(link["source"]), target=str(link["target"]))
        for link in data.get("links", [])
    ]
    unknown_nodes = {
        endpoint
        for edge in edges
        for endpoint in (edge.source, edge.target)
        if endpoint not in set(nodes)
    }
    if unknown_nodes:
        raise ValueError(
            f"{path}: links reference unknown nodes: {sorted(unknown_nodes)}"
        )
    return nodes, edges


def _biofabric_order(
    nodes: list[str], edges: list[Edge]
) -> tuple[list[str], list[Edge]]:
    """Sort nodes by incidence first, then sort edges Degreecending.

    All Rome graphs are single-depth graphs. Node ordering is stable for ties,
    as is JavaScript's modern Array.sort. Edge ordering follows the topmost
    endpoint and then edge length from the already ordered node list.
    """
    incidence = Counter(
        endpoint for edge in edges for endpoint in (edge.source, edge.target)
    )
    ordered_nodes = sorted(nodes, key=lambda node: -incidence[node])
    node_index = {node: index for index, node in enumerate(ordered_nodes)}
    ordered_edges = sorted(
        edges,
        key=lambda edge: (
            min(node_index[edge.source], node_index[edge.target]),
            abs(node_index[edge.source] - node_index[edge.target]),
        ),
    )
    return ordered_nodes, ordered_edges


def _natural_path_key(path: Path) -> tuple[tuple[int, object], ...]:
    """Sort filenames by numeric components rather than lexicographically."""
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part.casefold())
        for part in re.split(r"(\d+)", path.name)
        if part
    )


def calculate_graph_stats(path: Path) -> GraphStats:
    """Calculate edge statistics after incidence/Degreecending ordering."""
    nodes, edges = _read_graph(path)
    incidence = Counter(
        endpoint for edge in edges for endpoint in (edge.source, edge.target)
    )
    ordered_nodes, ordered_edges = _biofabric_order(nodes, edges)
    node_index = {node: index for index, node in enumerate(ordered_nodes)}

    # The uncollapsed layout gives every edge its own x coordinate. The
    # partially collapsed branch in the supplied JS reuses x for adjacent
    # edges with the same topmost node.
    topmost_nodes = [
        min(node_index[edge.source], node_index[edge.target]) for edge in ordered_edges
    ]
    partially_collapsed_lanes = sum(
        1
        for index, topmost_node in enumerate(topmost_nodes)
        if index == 0 or topmost_node != topmost_nodes[index - 1]
    )

    return GraphStats(
        name=path.name,
        node_count=len(nodes),
        edge_count=len(edges),
        uncollapsed_lanes=len(ordered_edges),
        partially_collapsed_lanes=partially_collapsed_lanes,
        layered_edges=len(ordered_edges) - partially_collapsed_lanes,
        average_degree=(2 * len(edges) / len(nodes)) if nodes else 0.0,
        maximum_degree=max((incidence[node] for node in nodes), default=0),
    )


def calculate_dataset_stats(data_dir: Path) -> list[GraphStats]:
    """Calculate stats for every JSON graph in human numeric filename order."""
    paths = sorted(data_dir.glob("*.json"), key=_natural_path_key)
    if not paths:
        raise FileNotFoundError(f"No JSON graph files found in {data_dir}")
    return [calculate_graph_stats(path) for path in paths]


def _print_stats(stats: Iterable[GraphStats]) -> None:
    rows = list(stats)
    print(
        "graph\tnodes\tedges\tuncollapsed lanes\tpartially collapsed lanes\t"
        "layered edges\tlane savings\taverage degree\tmaximum degree"
    )
    for row in rows:
        print(
            f"{row.name}\t{row.node_count}\t{row.edge_count}\t"
            f"{row.uncollapsed_lanes}\t{row.partially_collapsed_lanes}\t"
            f"{row.layered_edges}\t{row.lane_savings}\t"
            f"{row.average_degree:.2f}\t{row.maximum_degree}"
        )
    total_edges = sum(row.edge_count for row in rows)
    total_nodes = sum(row.node_count for row in rows)
    total_partial = sum(row.partially_collapsed_lanes for row in rows)
    total_layered = sum(row.layered_edges for row in rows)
    total_maximum_degree = max((row.maximum_degree for row in rows), default=0)
    print(
        f"TOTAL ({len(rows)} graphs)\t-\t{total_edges}\t{total_edges}\t"
        f"{total_partial}\t{total_layered}\t{total_edges - total_partial}\t"
        f"{(2 * total_edges / total_nodes) if total_nodes else 0.0:.2f}\t"
        f"{total_maximum_degree}"
    )
    print(
        f"AVERAGE\t-\t{total_edges / len(rows):.2f}\t"
        f"{total_edges / len(rows):.2f}\t{total_partial / len(rows):.2f}\t"
        f"{total_layered / len(rows):.2f}\t"
        f"{(total_edges - total_partial) / len(rows):.2f}\t"
        f"{sum(row.average_degree for row in rows) / len(rows):.2f}\t"
        f"{sum(row.maximum_degree for row in rows) / len(rows):.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data_dir",
        nargs="?",
        type=Path,
        default=Path("rome/data"),
        help="directory containing Rome node-link JSON files (default: rome/data)",
    )
    args = parser.parse_args()
    _print_stats(calculate_dataset_stats(args.data_dir))
