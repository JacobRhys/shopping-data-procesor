import argparse
import sqlite3
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import Dict

import pandas as pd
from unittest import mock

# Ensure project root is on sys.path for `app` imports when tests run from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import csv_to_sqlite


def _make_sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Member_number": [1, 1, 2, 2, 3, 3],
            "Date": [
                "01-01-2020",
                "01-01-2020",
                "02-01-2020",
                "02-01-2020",
                "03-01-2020",
                "03-01-2020",
            ],
            "itemDescription": [
                "bread",
                "milk",
                "bread",
                "butter",
                "butter",
                "milk",
            ],
        }
    )


class CsvToSqliteTests(unittest.TestCase):
    def test_build_purchase_id_formats_dd_mm_yyyy(self) -> None:
        df = pd.DataFrame(
            {
                "Member_number": [99],
                "Date": ["01-09-2023"],
            }
        )
        purchase_id = csv_to_sqlite.build_purchase_id(df)
        self.assertEqual(list(purchase_id), ["99020230901"])

    def test_compute_co_occurrences_counts_pairs(self) -> None:
        df = _make_sample_df()

        items, pair_counts = csv_to_sqlite.compute_co_occurrences(df)

        self.assertEqual(list(items), ["bread", "milk", "butter"])
        self.assertEqual(
            pair_counts,
            Counter(
                {
                    ("bread", "milk"): 1,
                    ("bread", "butter"): 1,
                    ("butter", "milk"): 1,
                }
            ),
        )

    def test_compute_co_occurrences_ignores_duplicate_items_in_same_purchase(self) -> None:
        df = pd.DataFrame(
            {
                "Member_number": [1, 1, 1],
                "Date": ["01-01-2020", "01-01-2020", "01-01-2020"],
                "itemDescription": ["bread", "bread", "milk"],
            }
        )
        items, pair_counts = csv_to_sqlite.compute_co_occurrences(df)

        self.assertEqual(list(items), ["bread", "milk"])
        # Duplicate bread in the same purchase should not double-count the pair.
        self.assertEqual(pair_counts, Counter({("bread", "milk"): 1}))

    def test_write_sqlite_persists_items_and_pairs(self) -> None:
        df = _make_sample_df()
        items, pair_counts = csv_to_sqlite.compute_co_occurrences(df)

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "co_occurrences.sqlite"
            csv_to_sqlite.write_sqlite(items, pair_counts, db_path)

            self.assertTrue(db_path.exists())

            conn = sqlite3.connect(db_path)
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, name FROM items")
                item_rows = cur.fetchall()
                name_by_id: Dict[int, str] = {row[0]: row[1] for row in item_rows}
                self.assertEqual(set(name_by_id.values()), {"bread", "milk", "butter"})

                cur.execute("SELECT item1_id, item2_id, count FROM co_occurrences")
                rows = cur.fetchall()
                self.assertEqual(len(rows), 3)  # undirected pairs only

                named_pairs = {
                    (name_by_id[a], name_by_id[b]): count for a, b, count in rows
                }
                self.assertEqual(
                    named_pairs,
                    {
                        ("bread", "milk"): 1,
                        ("bread", "butter"): 1,
                        ("butter", "milk"): 1,
                    },
                )
            finally:
                conn.close()

    def test_main_uses_defaults_when_no_args_provided(self) -> None:
        # Patch defaults to temp files so we don't touch real data.
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "input.csv"
            out_path = Path(tmpdir) / "out.sqlite"

            _make_sample_df().to_csv(csv_path, index=False)

            with mock.patch.object(csv_to_sqlite, "CSV_PATH", csv_path), mock.patch.object(
                csv_to_sqlite, "SQLITE_PATH", out_path
            ), mock.patch.object(
                csv_to_sqlite, "parse_args", return_value=argparse.Namespace(csv_path=None, out=None)
            ):
                csv_to_sqlite.main()

            self.assertTrue(out_path.exists())
            # Verify a known pair count exists.
            conn = sqlite3.connect(out_path)
            try:
                cur = conn.execute("SELECT count FROM co_occurrences WHERE count = 1")
                self.assertTrue(cur.fetchone())
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
