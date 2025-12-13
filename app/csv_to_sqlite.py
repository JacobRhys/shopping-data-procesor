"""
Load a grocery transactions CSV and write a SQLite DB with two tables:
- items: unique itemDescription values
- co_occurrences: undirected co-purchase counts between item pairs
"""

import argparse
import sqlite3
import pandas as pd
from collections import Counter
from itertools import combinations
from pathlib import Path

CSV_PATH = Path("data/Supermarket_dataset_PAI.csv")
SQLITE_PATH = Path("data/co_occurrences.sqlite")

def build_purchase_id(df: pd.DataFrame) -> pd.Series:
    date_str = pd.to_datetime(df["Date"], format="%d-%m-%Y").dt.strftime("%Y%m%d")
    return df["Member_number"].astype(str) + date_str


def compute_co_occurrences(df: pd.DataFrame) -> tuple[pd.Index, Counter]:
    df = df.copy()
    df["Purchace_ID"] = build_purchase_id(df)

    pair_counts: Counter[tuple[str, str]] = Counter()
    for _, group in df.groupby("Purchace_ID"):
        items = pd.unique(group["itemDescription"])
        for a, b in combinations(sorted(items), 2):
            pair_counts[(a, b)] += 1

    return pd.Index(pd.unique(df["itemDescription"])), pair_counts


def write_sqlite(items: pd.Index, pair_counts: Counter, out_path: Path) -> None:
    if out_path.exists():
        out_path.unlink()

    conn = sqlite3.connect(out_path)
    try:
        cur = conn.cursor()
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE items (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE co_occurrences (
                item1_id INTEGER NOT NULL,
                item2_id INTEGER NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (item1_id, item2_id),
                FOREIGN KEY (item1_id) REFERENCES items(id),
                FOREIGN KEY (item2_id) REFERENCES items(id)
            );
            """
        )

        cur.executemany("INSERT INTO items(name) VALUES (?)", [(item,) for item in items])
        conn.commit()

        item_id_map = {name: idx + 1 for idx, name in enumerate(items)}
        rows = [
            (item_id_map[a], item_id_map[b], cnt)
            for (a, b), cnt in pair_counts.items()
        ]
        cur.executemany(
            "INSERT INTO co_occurrences(item1_id, item2_id, count) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert grocery CSV into SQLite with item list and co-occurrence counts.",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to input CSV (default: data/Supermarket_dataset_PAI.csv).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output SQLite DB path (default: data/co_occurrences.sqlite).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = args.csv_path or CSV_PATH
    out_path = args.out or SQLITE_PATH

    df = pd.read_csv(csv_path)
    items, pair_counts = compute_co_occurrences(df)
    write_sqlite(items, pair_counts, out_path)
    print(f"Wrote {len(items)} items and {len(pair_counts)} co-occurrence rows to {out_path}")


if __name__ == "__main__":
    main()
