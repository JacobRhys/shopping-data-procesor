import sys
import unittest
from pathlib import Path

import numpy as np

# Ensure project root is on sys.path for imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.co_occurrence_store import CoOccurrenceStore  # type: ignore
from app.embedding_cpu import (build_dense_matrix,  # type: ignore
                               compute_svd_embeddings, recommend_for_basket,
                               recommend_for_customer, recommend_for_item)


class EmbeddingTests(unittest.TestCase):
    def setUp(self) -> None:
        store = CoOccurrenceStore()
        store.add_transaction(["a", "b", "c"])
        store.add_transaction(["a", "b"])
        store.add_transaction(["b", "c"])
        self.store = store

    def test_build_dense_matrix(self) -> None:
        mat, items = build_dense_matrix(self.store)
        self.assertEqual(mat.shape, (3, 3))
        self.assertEqual(items, ["a", "b", "c"])
        # Symmetric counts
        self.assertEqual(mat[0, 1], mat[1, 0])
        self.assertGreater(mat[0, 1], 0)

    def test_compute_svd_embeddings(self) -> None:
        mat, _ = build_dense_matrix(self.store)
        emb = compute_svd_embeddings(mat, k=2)
        self.assertEqual(emb.shape, (3, 2))

    def test_recommend_for_item(self) -> None:
        mat, items = build_dense_matrix(self.store)
        emb = compute_svd_embeddings(mat, k=2)
        recs = recommend_for_item(items, emb, "a", top_k=2)
        self.assertTrue(recs)
        self.assertEqual(len(recs), 2)
        self.assertNotEqual(recs[0][0], "a")

    def test_recommend_for_basket(self) -> None:
        mat, items = build_dense_matrix(self.store)
        emb = compute_svd_embeddings(mat, k=2)
        recs = recommend_for_basket(items, emb, ["a", "b"], top_k=2)
        self.assertTrue(recs)
        # No recommendations should include existing basket items.
        rec_item_names = {r[0] for r in recs}
        self.assertFalse({"a", "b"} & rec_item_names)

    def test_recommend_for_customer(self) -> None:
        mat, items = build_dense_matrix(self.store)
        emb = compute_svd_embeddings(mat, k=2)
        recs = recommend_for_customer(items, emb, ["a"], top_k=2)
        self.assertTrue(recs)
        rec_item_names = {r[0] for r in recs}
        self.assertNotIn("a", rec_item_names)


if __name__ == "__main__":
    unittest.main()
