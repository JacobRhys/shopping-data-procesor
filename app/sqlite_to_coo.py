"""
Load co-occurrence data from SQLite into the in-memory CoOccurrenceStore.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from .co_occurrence_store import CoOccurrenceStore

SQLITE_PATH = Path("data/co_occurrences.sqlite")


def load_store(db_path: Path) -> CoOccurrenceStore:
    """
    Reconstruct a CoOccurrenceStore from the SQLite persistence layer.
    """
    store = CoOccurrenceStore()
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM items ORDER BY id")
        id_to_name = {row[0]: row[1] for row in cur.fetchall()}

        # Preload items in ID order to maintain determinism.
        for _, name in sorted(id_to_name.items()):
            store.add_item(name)

        cur.execute("SELECT item1_id, item2_id, count FROM co_occurrences")
        for item1_id, item2_id, count in cur.fetchall():
            store.add_pair_count(id_to_name[item1_id], id_to_name[item2_id], count)

        return store
    finally:
        conn.close()
