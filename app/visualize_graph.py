"""3D network visualizer for co-occurrence data."""

from __future__ import annotations

import sys
from math import log1p, sqrt
from pathlib import Path
from typing import Optional

# Allow running as a script without package context.
if __package__ is None or __package__ == "":
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from app.sqlite_to_coo import load_store  # type: ignore
else:
    from .sqlite_to_coo import load_store


def _require_visual_deps():
    try:
        import matplotlib.pyplot as plt  # type: ignore
        import networkx as nx  # type: ignore
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Visualization requires matplotlib and networkx. "
            "Install with: pip install matplotlib networkx"
        ) from exc
    return plt, nx


def build_graph(
    store,
    min_count: int = 1,
    top_edges: Optional[int] = 200,
    include_isolated: bool = True,
):
    """Build a NetworkX graph with optional filtering."""
    _, nx = _require_visual_deps()

    pairs = [
        ((a, b), count) for (a, b), count in store.iter_pairs() if count >= min_count
    ]
    pairs.sort(key=lambda entry: -entry[1])
    if top_edges is not None:
        pairs = pairs[:top_edges]

    graph = nx.Graph()
    if include_isolated:
        graph.add_nodes_from(store.items())
    for (a, b), count in pairs:
        graph.add_edge(a, b, weight=count)
    return graph


def draw_graph_3d(graph) -> None:
    """Render the graph in 3D using a spring layout."""
    plt, nx = _require_visual_deps()
    if graph.number_of_nodes() == 0:
        raise ValueError("Graph is empty; add items or relax filters.")

    weights = [data["weight"] for _, _, data in graph.edges(data=True)]
    max_w = max(weights)
    edge_widths = [1.5 + 4.5 * (log1p(w) / log1p(max_w)) for w in weights]
    cmap = plt.get_cmap("viridis")
    edge_colors = [cmap(w / max_w) for w in weights]

    k = 5.0 / sqrt(max(graph.number_of_nodes(), 1))
    pos = nx.spring_layout(
        graph,
        seed=42,
        dim=3,
        k=k,  # larger k spreads nodes farther apart
        iterations=500,
    )
    # Optionally push points further apart by scaling coordinates.
    pos = {n: coords * 1.8 for n, coords in pos.items()}
    xs = [pos[n][0] for n in graph.nodes()]
    ys = [pos[n][1] for n in graph.nodes()]
    zs = [pos[n][2] for n in graph.nodes()]

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    # Draw edges
    for (u, v), width, color in zip(graph.edges(), edge_widths, edge_colors):
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        z = [pos[u][2], pos[v][2]]
        ax.plot(x, y, z, color=color, linewidth=width, alpha=0.9)

    # Draw nodes
    ax.scatter(xs, ys, zs, s=120, c="#4c72b0", alpha=0.95, depthshade=True)

    # Draw labels
    for node, (x, y, z) in pos.items():
        ax.text(x, y, z, node, fontsize=8, color="black")

    ax.set_title("3D Co-occurrence Graph")
    ax.set_axis_off()
    plt.tight_layout()
    plt.show()


def _prompt_with_default(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def run_interactive() -> None:
    """Interactive entry point using input() prompts."""
    sqlite_default = "data/co_occurrences.sqlite"
    min_count_default = "1"
    top_edges_default = "100"

    sqlite_path = sqlite_default
    min_count = int(_prompt_with_default("Minimum edge count", min_count_default))
    top_edges_raw = _prompt_with_default("Top N edges (0 for all)", top_edges_default)
    top_edges: Optional[int] = int(top_edges_raw)
    if top_edges <= 0:
        top_edges = None

    include_isolated_raw = _prompt_with_default(
        "Include isolated nodes? (y/n)", "n"
    ).lower()
    include_isolated = include_isolated_raw.startswith("y")

    store = load_store(sqlite_path)
    graph = build_graph(
        store,
        min_count=min_count,
        top_edges=top_edges,
        include_isolated=include_isolated,
    )
    draw_graph_3d(graph)


if __name__ == "__main__":
    run_interactive()
