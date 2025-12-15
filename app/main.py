"""
Simple CLI for exploring supermarket co-occurrence data.

Commands (type `help` inside the CLI):
- help / quit
- build [csv_path] [sqlite_out]   -> compute pairs from CSV and write SQLite
- load [sqlite_path]              -> load store into memory
- stats                           -> show number of items and pairs
- top_with <item> [k]             -> show top co-purchases with an item
- top_pairs [k]                   -> show top global pairs
- count <item_a> <item_b>         -> show co-occurrence count for a pair
- visualize                       -> launch the 3D visualizer prompts
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

# Allow running as a script by ensuring package is on sys.path.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from app import (
    CoOccurrenceStore,
    are_often_copurchased,  # type: ignore
    build_dense_matrix,
    compute_co_occurrences,
    compute_svd_embeddings,
    recommend_for_basket,
    recommend_for_customer,
    recommend_for_item,
    top_pairs,
    top_with_item,
    write_sqlite,
)
from app.asci_table import table_draw  # type: ignore
from app.csv_to_sqlite import CSV_PATH, SQLITE_PATH
from app.sqlite_to_coo import load_store  # type: ignore
from app.visualize_graph import run_interactive as visualize_interactive  # type: ignore


def help_command() -> None:
    header = [("Command", "Description", "Args")]
    commands = [
        ("help", "List commands", "n/a"),
        ("quit", "Exit the CLI", "n/a"),
        ("build", "Build SQLite from CSV", "[csv_path] [sqlite_out]"),
        ("load", "Load store from SQLite", "[sqlite_path]"),
        ("stats", "Show item and pair counts", "n/a"),
        ("top_with", "Top co-purchases for item", "item [k]"),
        ("top_pairs", "Top pairs overall", "[k]"),
        ("count", "Count for an item pair", "item_a item_b"),
        ("visualize", "Launch 3D graph viewer", "prompts for options"),
        ("related", "BFS up to depth for related items", "item [depth]"),
        ("rec_item", "Embedding-based rec for one item", "item [k]"),
        (
            "rec_basket",
            "Embedding rec for basket (comma-separated)",
            "item1,item2,... [k]",
        ),
        ("rec_customer", "Embedding rec for purchased items", "item1,item2,... [k]"),
    ]
    print(table_draw(header + commands))


def format_pairs(rows: Iterable[tuple[tuple[str, str], int]]) -> str:
    table = [("Item A", "Item B", "Count")]
    for (a, b), cnt in rows:
        table.append((a, b, str(cnt)))
    return table_draw(table)


def format_neighbors(rows: Iterable[tuple[str, int]], item: str) -> str:
    table = [(f"Items bought with '{item}'", "Count")]
    for other, cnt in rows:
        table.append((other, str(cnt)))
    return table_draw(table)


def build_command(csv_path: Optional[str], sqlite_out: Optional[str]) -> None:
    csv_src = Path(csv_path) if csv_path else CSV_PATH
    sqlite_dest = Path(sqlite_out) if sqlite_out else SQLITE_PATH
    df = pd.read_csv(csv_src)
    items, pair_counts = compute_co_occurrences(df)
    write_sqlite(items, pair_counts, sqlite_dest)
    print(f"Wrote {len(items)} items and {len(pair_counts)} pairs to {sqlite_dest}")


def run_loop(command_source: Optional[Iterable[str]] = None) -> None:
    print(
        "\nSupermarket co-occurrence CLI\n"
        "Type 'help' for commands, 'quit' to exit.\n"
    )

    commands_iter = iter(command_source) if command_source is not None else None
    store: Optional[CoOccurrenceStore] = None
    embeddings = None
    items_for_emb = None
    current_db = SQLITE_PATH

    while True:
        raw = next(commands_iter) if commands_iter is not None else input(">>> ")
        if raw is None:
            continue
        try:
            parts = shlex.split(raw)
        except ValueError as exc:
            print(f"Error parsing input: {exc}")
            continue
        if not parts:
            continue

        cmd = parts[0]
        args = parts[1:]

        try:
            if cmd == "help":
                help_command()
            elif cmd == "quit":
                print("Goodbye!")
                break
            elif cmd == "build":
                csv_arg = args[0] if len(args) >= 1 else None
                out_arg = args[1] if len(args) >= 2 else None
                build_command(csv_arg, out_arg)
                # If we just built a DB, make it the current default.
                if out_arg:
                    current_db = Path(out_arg)
            elif cmd == "load":
                db_arg = Path(args[0]) if args else current_db
                store = load_store(db_arg)
                current_db = db_arg
                embeddings = None
                items_for_emb = None
                print(f"Loaded store from {db_arg}")
            elif cmd == "stats":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                num_items = len(store.items())
                num_pairs = sum(1 for _ in store.iter_pairs())
                print(f"Items: {num_items}, Pairs: {num_pairs}")
            elif cmd == "top_with":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                if not args:
                    print("Usage: top_with <item> [k]")
                    continue
                item = args[0]
                k = int(args[1]) if len(args) >= 2 else 5
                rows = top_with_item(store, item, limit=k)
                print(format_neighbors(rows, item))
            elif cmd == "top_pairs":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                k = int(args[0]) if args else 5
                rows = top_pairs(store, limit=k)
                print(format_pairs(rows))
            elif cmd == "count":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                if len(args) < 2:
                    print("Usage: count <item_a> <item_b>")
                    continue
                a, b = args[0], args[1]
                cnt = store.get_count(a, b)
                print(f"'{a}' with '{b}': {cnt}")
                if are_often_copurchased(store, a, b, min_count=1):
                    print("They co-occur at least once.")
            elif cmd == "visualize":
                visualize_interactive()
            elif cmd == "related":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                if not args:
                    print("Usage: related <item> [depth]")
                    continue
                item = args[0]
                depth = int(args[1]) if len(args) >= 2 else 2
                neighbors = store.bfs_related(item, depth=depth)
                if neighbors:
                    print(
                        f"Items within depth {depth} of '{item}': {', '.join(neighbors)}"
                    )
                else:
                    print(f"No related items within depth {depth} for '{item}'.")
            elif cmd == "rec_item":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                if not args:
                    print("Usage: rec_item <item> [k]")
                    continue
                item = args[0]
                k = int(args[1]) if len(args) >= 2 else 5
                if embeddings is None or items_for_emb is None:
                    mat, items_for_emb = build_dense_matrix(store)
                    embeddings = compute_svd_embeddings(
                        mat, k=min(20, len(items_for_emb))
                    )
                recs = recommend_for_item(items_for_emb, embeddings, item, top_k=k)
                if recs:
                    print(
                        table_draw(
                            [("Item", "Similarity")]
                            + [(n, f"{s:.3f}") for n, s in recs]
                        )
                    )
                else:
                    print(f"No recommendations for '{item}'.")
            elif cmd == "rec_basket":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                if not args:
                    print("Usage: rec_basket <item1,item2,...> [k]")
                    continue
                basket_items = [p.strip() for p in args[0].split(",") if p.strip()]
                k = int(args[1]) if len(args) >= 2 else 5
                if embeddings is None or items_for_emb is None:
                    mat, items_for_emb = build_dense_matrix(store)
                    embeddings = compute_svd_embeddings(
                        mat, k=min(20, len(items_for_emb))
                    )
                recs = recommend_for_basket(
                    items_for_emb, embeddings, basket_items, top_k=k
                )
                if recs:
                    print(
                        table_draw(
                            [("Item", "Similarity")]
                            + [(n, f"{s:.3f}") for n, s in recs]
                        )
                    )
                else:
                    print("No basket recommendations.")
            elif cmd == "rec_customer":
                if store is None:
                    print("No store loaded. Use 'load' first.")
                    continue
                if not args:
                    print("Usage: rec_customer <item1,item2,...> [k]")
                    continue
                purchased = [p.strip() for p in args[0].split(",") if p.strip()]
                k = int(args[1]) if len(args) >= 2 else 5
                if embeddings is None or items_for_emb is None:
                    mat, items_for_emb = build_dense_matrix(store)
                    embeddings = compute_svd_embeddings(
                        mat, k=min(20, len(items_for_emb))
                    )
                recs = recommend_for_customer(
                    items_for_emb, embeddings, purchased, top_k=k
                )
                if recs:
                    print(
                        table_draw(
                            [("Item", "Similarity")]
                            + [(n, f"{s:.3f}") for n, s in recs]
                        )
                    )
                else:
                    print("No customer recommendations.")
            else:
                print(f"Unknown command: {cmd}. Type 'help' for options.")
        except Exception as exc:
            print(f"Error: {exc}")


def main() -> None:
    run_loop()


if __name__ == "__main__":
    main()
