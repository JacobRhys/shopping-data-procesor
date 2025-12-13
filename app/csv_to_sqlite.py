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

def build_purchase_id(df: pd.DataFrame) -> pd.Series:
    pass

def compute_co_occurrences(df: pd.DataFrame) -> tuple[pd.Index, Counter]:
    pass


def write_sqlite(items: pd.Index, pair_counts: Counter, out_path: Path) -> None:
    pass


def parse_args() -> argparse.Namespace:
    pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
