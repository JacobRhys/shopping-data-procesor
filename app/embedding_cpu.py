"""
NumPy-based item embeddings from co-occurrence counts.

Provides:
- build_dense_matrix: create a symmetric item–item matrix from the store.
- compute_svd_embeddings: low-rank embedding via NumPy SVD.
- recommend_for_item: cosine-similarity recommendations for a single item.
- recommend_for_basket: recommendations given multiple items.

This mirrors the latent-factor flow described in cuda_use.md but stays CPU/NumPy-only.
"""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from .co_occurrence_store import CoOccurrenceStore


def build_dense_matrix(store: CoOccurrenceStore) -> Tuple[np.ndarray, List[str]]:
    """
    Build a dense symmetric matrix M where M[i, j] is the co-occurrence count
    between items[i] and items[j].
    """
    items = store.items()
    n = len(items)
    mat = np.zeros((n, n), dtype=float)
    name_to_idx = {name: i for i, name in enumerate(items)}

    for (a, b), count in store.iter_pairs():
        i, j = name_to_idx[a], name_to_idx[b]
        mat[i, j] = count
        mat[j, i] = count  # symmetric
    return mat, items


def compute_svd_embeddings(matrix: np.ndarray, k: int = 20) -> np.ndarray:
    """
    Compute a low-rank embedding from the co-occurrence matrix using NumPy SVD.
    Returns an (n x k) matrix where each row is an item embedding.
    """
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be square")
    n = matrix.shape[0]
    k = max(1, min(k, n))

    # Full SVD then truncate; fine for small n (e.g., 167 items).
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    u_k = u[:, :k]
    s_k = s[:k]
    # Scale left singular vectors by singular values to get embeddings.
    return u_k * s_k


def _normalize_rows(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return mat / norms


def recommend_for_item(
    items: Sequence[str],
    embeddings: np.ndarray,
    item: str,
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Recommend top_k items similar to the given item using cosine similarity.
    """
    name_to_idx = {name: i for i, name in enumerate(items)}
    if item not in name_to_idx or top_k <= 0:
        return []

    idx = name_to_idx[item]
    vecs = _normalize_rows(embeddings)
    sims = vecs @ vecs[idx]
    sims[idx] = -math.inf  # exclude self
    top_idx = np.argsort(-sims)[:top_k]
    return [(items[i], float(sims[i])) for i in top_idx]


def recommend_for_basket(
    items: Sequence[str],
    embeddings: np.ndarray,
    basket: Iterable[str],
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Recommend items for a basket by averaging embedding vectors for the basket items.
    """
    name_to_idx = {name: i for i, name in enumerate(items)}
    idxs = [name_to_idx[b] for b in basket if b in name_to_idx]
    if not idxs or top_k <= 0:
        return []

    vecs = _normalize_rows(embeddings)
    basket_vec = vecs[idxs].mean(axis=0)
    candidate_idx = [i for i in range(len(items)) if i not in idxs]
    if not candidate_idx:
        return []
    sims = vecs[candidate_idx] @ basket_vec
    order = np.argsort(-sims)[:top_k]
    return [
        (items[candidate_idx[i]], float(sims[i]))
        for i in order
    ]


def recommend_for_customer(
    items: Sequence[str],
    embeddings: np.ndarray,
    purchased: Iterable[str],
    top_k: int = 5,
) -> List[Tuple[str, float]]:
    """
    Recommend items not yet purchased by averaging embeddings of all purchased items.
    """
    name_to_idx = {name: i for i, name in enumerate(items)}
    idxs = [name_to_idx[p] for p in purchased if p in name_to_idx]
    if not idxs or top_k <= 0:
        return []

    vecs = _normalize_rows(embeddings)
    profile = vecs[idxs].mean(axis=0)
    candidate_idx = [i for i in range(len(items)) if i not in idxs]
    if not candidate_idx:
        return []
    sims = vecs[candidate_idx] @ profile
    order = np.argsort(-sims)[:top_k]
    return [
        (items[candidate_idx[i]], float(sims[i]))
        for i in order
    ]
