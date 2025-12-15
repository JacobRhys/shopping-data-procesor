"""
Lightweight Flask UI for exploring supermarket co-occurrence data.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

import networkx as nx
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, render_template, request

# Ensure local imports work whether run as script or module.
ROOT = Path(__file__).resolve().parent
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (
    build_dense_matrix,
    compute_svd_embeddings,  # type: ignore
    recommend_for_basket,
    recommend_for_item,
    top_pairs,
    top_with_item,
)
from app.sqlite_to_coo import load_store  # type: ignore

DEFAULT_DB = ROOT / "data" / "co_occurrences.sqlite"

app = Flask(__name__, template_folder=str(ROOT / "frontend"))

# Load store once at startup (if available).
try:
    STORE = load_store(DEFAULT_DB)
except Exception:
    STORE = None


def _ensure_embeddings(store) -> tuple[Sequence[str], np.ndarray]:
    mat, items = build_dense_matrix(store)
    emb = compute_svd_embeddings(mat, k=min(20, len(items)))
    return items, emb


def _network_html(store, top_edges: int = 150, min_count: int = 1) -> Optional[str]:
    pairs = [((a, b), c) for (a, b), c in store.iter_pairs() if c >= min_count]
    pairs.sort(key=lambda x: -x[1])
    pairs = pairs[:top_edges]
    if not pairs:
        return None

    g = nx.Graph()
    for (a, b), c in pairs:
        g.add_edge(a, b, weight=c)

    k = 3.0 / max(len(g.nodes), 1) ** 0.5
    pos = nx.spring_layout(g, dim=3, seed=42, k=k, iterations=400)

    node_x = [pos[n][0] for n in g.nodes]
    node_y = [pos[n][1] for n in g.nodes]
    node_z = [pos[n][2] for n in g.nodes]
    node_text = [n for n in g.nodes]

    node_trace = go.Scatter3d(
        x=node_x,
        y=node_y,
        z=node_z,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
        marker=dict(size=6, color="#2563eb", opacity=0.9),
        textfont=dict(color="#111827", size=10),
    )

    edge_traces = []
    max_w = max(c for _, c in pairs)
    for (a, b), c in pairs:
        x0, y0, z0 = pos[a]
        x1, y1, z1 = pos[b]
        color = px.colors.sample_colorscale("viridis", c / max_w)[0]
        edge_traces.append(
            go.Scatter3d(
                x=[x0, x1, None],
                y=[y0, y1, None],
                z=[z0, z1, None],
                mode="lines",
                line=dict(color=color, width=2 + 4 * (c / max_w)),
                hoverinfo="text",
                hovertext=f"{a} \u2013 {b}: {c}",
                opacity=0.9,
            )
        )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
        title="3D Co-occurrence Network (top edges)",
    )
    return go.Figure.to_html(fig, include_plotlyjs="cdn", full_html=False)


@app.route("/", methods=["GET"])
def dashboard():
    item = (request.args.get("item") or "").strip()
    basket_raw = (request.args.get("basket") or "").strip()
    top_n = int(request.args.get("k") or "5")

    store_missing = STORE is None
    top_pairs_rows: List[tuple[tuple[str, str], int]] = []
    top_with_rows: List[tuple[str, int]] = []
    rec_item_rows: List[tuple[str, float]] = []
    rec_basket_rows: List[tuple[str, float]] = []
    error_msg: Optional[str] = None
    network_html: Optional[str] = None

    if not store_missing:
        try:
            top_pairs_rows = top_pairs(STORE, limit=top_n)
            if item:
                top_with_rows = top_with_item(STORE, item, limit=top_n)
            items, emb = _ensure_embeddings(STORE)
            if item:
                rec_item_rows = recommend_for_item(items, emb, item, top_k=top_n)
            if basket_raw:
                basket_items = [p.strip() for p in basket_raw.split(",") if p.strip()]
                rec_basket_rows = recommend_for_basket(
                    items, emb, basket_items, top_k=top_n
                )
            network_html = _network_html(STORE, top_edges=180, min_count=1)
        except Exception as exc:  # pragma: no cover - defensive for runtime
            error_msg = str(exc)
    else:
        error_msg = f"No SQLite data found at {DEFAULT_DB}"

    return render_template(
        "dashboard.html",
        item=item,
        basket=basket_raw,
        top_n=top_n,
        store_missing=store_missing,
        top_pairs_rows=top_pairs_rows,
        top_with_rows=top_with_rows,
        rec_item_rows=rec_item_rows,
        rec_basket_rows=rec_basket_rows,
        error=error_msg,
        db_path=str(DEFAULT_DB),
        network_html=network_html,
    )


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    app.run(debug=True, port=5000)
