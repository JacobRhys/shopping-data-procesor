import sys
import unittest
from pathlib import Path

# Ensure project root is on sys.path for `app` imports when tests run from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import CoOccurrenceStore


class CoOccurrenceStoreTests(unittest.TestCase):
    def test_add_item_assigns_incremental_ids_and_stores_names(self) -> None:
        store = CoOccurrenceStore()

        bread_id = store.add_item("bread")
        milk_id = store.add_item("milk")
        # Adding an existing item returns the same id.
        repeat_id = store.add_item("bread")

        self.assertEqual(bread_id, 0)
        self.assertEqual(milk_id, 1)
        self.assertEqual(repeat_id, bread_id)
        self.assertEqual(store.items(), ["bread", "milk"])

    def test_add_pair_stores_counts_symmetrically(self) -> None:
        store = CoOccurrenceStore()

        store.add_pair("bread", "milk")
        store.add_pair("milk", "bread")  # Same pair, different order.

        self.assertEqual(store.get_count("bread", "milk"), 2)
        self.assertEqual(store.get_count("milk", "bread"), 2)
        self.assertEqual(store.get_count("bread", "butter"), 0)  # unseen

    def test_add_pair_ignores_self_pairs(self) -> None:
        store = CoOccurrenceStore()

        store.add_pair("bread", "bread")

        self.assertEqual(store.items(), ["bread"])
        self.assertEqual(store.get_count("bread", "bread"), 0)

    def test_add_transaction_deduplicates_items_within_purchase(self) -> None:
        store = CoOccurrenceStore()

        store.add_transaction(["bread", "bread", "milk"])

        self.assertEqual(store.get_count("bread", "milk"), 1)
        self.assertEqual(store.items(), ["bread", "milk"])

    def test_add_transaction_accumulates_over_multiple_calls(self) -> None:
        store = CoOccurrenceStore()

        store.add_transaction(["bread", "milk"])
        store.add_transaction(["bread", "butter"])
        store.add_transaction(["milk", "butter"])

        self.assertEqual(store.get_count("bread", "milk"), 1)
        self.assertEqual(store.get_count("bread", "butter"), 1)
        self.assertEqual(store.get_count("milk", "butter"), 1)

    def test_iter_pairs_yields_all_pairs_with_counts(self) -> None:
        store = CoOccurrenceStore()
        store.add_transaction(["bread", "milk", "butter"])
        store.add_transaction(["bread", "butter"])

        pairs = dict(store.iter_pairs())
        self.assertEqual(
            pairs,
            {
                ("bread", "milk"): 1,
                ("bread", "butter"): 2,
                ("milk", "butter"): 1,
            },
        )

    def test_add_pair_count_accumulates_existing_pairs(self) -> None:
        store = CoOccurrenceStore()
        store.add_pair("bread", "milk")

        store.add_pair_count("bread", "milk", 3)

        self.assertEqual(store.get_count("bread", "milk"), 4)
        # Adding with reversed order should still increment the same pair.
        store.add_pair_count("milk", "bread", 2)
        self.assertEqual(store.get_count("bread", "milk"), 6)

    def test_add_pair_count_ignores_non_positive_and_handles_self_pairs(self) -> None:
        store = CoOccurrenceStore()

        store.add_pair_count("bread", "bread", 5)  # should only register item
        store.add_pair_count("bread", "milk", 0)   # ignored
        store.add_pair_count("bread", "milk", -2)  # ignored

        self.assertEqual(store.items(), ["bread"])
        self.assertEqual(store.get_count("bread", "bread"), 0)
        self.assertEqual(store.get_count("bread", "milk"), 0)


if __name__ == "__main__":
    unittest.main()
