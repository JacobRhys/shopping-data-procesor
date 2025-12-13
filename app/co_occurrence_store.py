'''
In-memory sparse co-occurrence store for grocery items.

This module maps item names to integer IDs and tracks undirected co-purchase
counts using a nested dictionary keyed by ordered item ID pairs.

realisticly id just use a built in sparse matrix and this is very much inspired 
by a sparse matrix implementation but I need to show that I am able to do this.
'''

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import DefaultDict, Dict, Iterable, Iterator, List, Tuple


class CoOccurrenceStore:
    '''
    Sparse undirected co-occurrence structure.

    Internally stores counts only once per pair using ordered item IDs:
    counts[min_id][max_id] = frequency.
    '''

    def __init__(self) -> None:
        self._item_to_id: Dict[str, int] = {}
        self._id_to_item: List[str] = []
        self._counts: DefaultDict[int, Dict[int, int]] = defaultdict(dict)

    def add_item(self, name: str) -> int:
        '''Add an item name if missing and return its ID.'''
        if name in self._item_to_id:
            return self._item_to_id[name]

        new_id = len(self._id_to_item)
        self._item_to_id[name] = new_id
        self._id_to_item.append(name)
        return new_id

    def _get_or_create_id(self, name: str) -> int:
        return self.add_item(name)

    def add_pair(self, item_a: str, item_b: str) -> None:
        '''
        Increment the co-occurrence count for a pair of item names.

        Pairs are stored in ordered ID form (min_id, max_id) to keep the
        structure symmetric. Self-pairs are ignored.
        '''
        if item_a == item_b:
            # Record the item but do not count self-pairs.
            self.add_item(item_a)
            return

        a_id = self._get_or_create_id(item_a)
        b_id = self._get_or_create_id(item_b)
        low, high = sorted((a_id, b_id))

        inner = self._counts[low]
        inner[high] = inner.get(high, 0) + 1

    def add_transaction(self, items: Iterable[str]) -> None:
        '''
        Update counts for all unique item pairs in a single transaction.

        Duplicate items within the same transaction are deduplicated.
        '''
        unique_items_in_order = dict.fromkeys(items)
        for item_a, item_b in combinations(unique_items_in_order, 2):
            self.add_pair(item_a, item_b)

    def get_count(self, item_a: str, item_b: str) -> int:
        '''Return the frequency for a pair of item names (0 if unseen).'''
        if item_a not in self._item_to_id or item_b not in self._item_to_id:
            return 0

        a_id = self._item_to_id[item_a]
        b_id = self._item_to_id[item_b]
        low, high = sorted((a_id, b_id))
        return self._counts.get(low, {}).get(high, 0)

    def iter_pairs(self) -> Iterator[Tuple[Tuple[str, str], int]]:
        '''Yield ((item_a, item_b), count) for all stored pairs.'''
        for low_id, inner in self._counts.items():
            for high_id, count in inner.items():
                yield (self._id_to_item[low_id], self._id_to_item[high_id]), count

    def items(self) -> List[str]:
        '''Return all known item names in ID order.'''
        return list(self._id_to_item)
