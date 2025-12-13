import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root is on sys.path for `app` imports when tests run from anywhere.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import CoOccurrenceStore, load_store


class SqliteToCooTests(unittest.TestCase):
    def _write_sample_db(self, db_path: Path) -> None:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.executescript(
                """
                CREATE TABLE items (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                );
                CREATE TABLE co_occurrences (
                    item1_id INTEGER NOT NULL,
                    item2_id INTEGER NOT NULL,
                    count INTEGER NOT NULL
                );
                """
            )
            # Insert with non-alphabetical order to ensure ID ordering is respected.
            cur.executemany(
                "INSERT INTO items(id, name) VALUES (?, ?)",
                [
                    (2, "banana"),
                    (1, "apple"),
                    (3, "carrot"),
                ],
            )
            cur.executemany(
                "INSERT INTO co_occurrences(item1_id, item2_id, count) VALUES (?, ?, ?)",
                [
                    (1, 2, 5),  # apple-banana
                    (1, 3, 2),  # apple-carrot
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def test_load_store_reconstructs_items_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "co_occurrences.sqlite"
            self._write_sample_db(db_path)

            store = load_store(db_path)

            self.assertIsInstance(store, CoOccurrenceStore)
            # Items come back in ID order, not alphabetical.
            self.assertEqual(store.items(), ["apple", "banana", "carrot"])
            self.assertEqual(store.get_count("apple", "banana"), 5)
            self.assertEqual(store.get_count("banana", "apple"), 5)
            self.assertEqual(store.get_count("apple", "carrot"), 2)
            self.assertEqual(store.get_count("banana", "carrot"), 0)


if __name__ == "__main__":
    unittest.main()
