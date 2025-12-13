"""
Lightweight Flask UI for exploring supermarket co-occurrence data.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from flask import Flask, render_template, request
import numpy as np

# Ensure local imports work whether run as script or module.
ROOT = Path(__file__).resolve().parent
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (  # type: ignore
    build_dense_matrix,
    compute_svd_embeddings,
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
                rec_basket_rows = recommend_for_basket(items, emb, basket_items, top_k=top_n)
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
    )


def create_app() -> Flask:
    return app


if __name__ == "__main__":
    app.run(debug=True, port=5000)
