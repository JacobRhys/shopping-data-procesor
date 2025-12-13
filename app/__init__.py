"""App package exports."""

from .csv_to_sqlite import build_purchase_id, compute_co_occurrences, write_sqlite
from .co_occurrence_store import CoOccurrenceStore
from .sqlite_to_coo import load_store
from .query import are_often_copurchased, top_pairs, top_with_item
from .embedding_cpu import (
    build_dense_matrix,
    compute_svd_embeddings,
    recommend_for_item,
    recommend_for_basket,
)

__all__ = [
    "build_purchase_id",
    "compute_co_occurrences",
    "write_sqlite",
    "CoOccurrenceStore",
    "load_store",
    "top_with_item",
    "top_pairs",
    "are_often_copurchased",
    "build_dense_matrix",
    "compute_svd_embeddings",
    "recommend_for_item",
    "recommend_for_basket",
]
