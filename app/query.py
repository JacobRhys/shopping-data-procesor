"""Query helpers for co-occurrence analysis."""

from __future__ import annotations

from typing import List, Tuple

from .co_occurrence_store import CoOccurrenceStore


def top_with_item(
    store: CoOccurrenceStore, item: str, limit: int = 5
) -> List[Tuple[str, int]]:
    """
    Return the most frequent co-purchases with a given item.

    Results are sorted by descending count, then alphabetically for determinism.
    Unknown items return an empty list.
    """
    if limit <= 0 or item not in store.items():
        return []

    neighbors: List[Tuple[str, int]] = []
    for (a, b), count in store.iter_pairs():
        if a == item:
            neighbors.append((b, count))
        elif b == item:
            neighbors.append((a, count))

    neighbors.sort(key=lambda pair: (-pair[1], pair[0]))
    return neighbors[:limit]


def top_pairs(store: CoOccurrenceStore, limit: int = 5):
    """
    Return the top item pairs across all transactions, sorted by frequency.
    """
    if limit <= 0:
        return []

    pairs = list(store.iter_pairs())
    pairs.sort(key=lambda entry: (-entry[1], entry[0][0], entry[0][1]))
    return pairs[:limit]


def are_often_copurchased(
    store: CoOccurrenceStore, item_a: str, item_b: str, min_count: int = 1
) -> bool:
    """
    Convenience predicate to check whether two items meet a minimum co-purchase count.
    """
    return store.get_count(item_a, item_b) >= min_count
