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
        pass

    def _get_or_create_id(self, name: str) -> int:
        pass
    
    def add_pair(self, item_a: str, item_b: str) -> None:
        '''
        Increment the co-occurrence count for a pair of item names.

        Pairs are stored in ordered ID form (min_id, max_id) to keep the
        structure symmetric. Self-pairs are ignored.
        '''
        pass

    def add_transaction(self, items: Iterable[str]) -> None:
        '''
        Update counts for all unique item pairs in a single transaction.

        Duplicate items within the same transaction are deduplicated.
        '''
        pass

    def get_count(self, item_a: str, item_b: str) -> int:
        '''Return the frequency for a pair of item names (0 if unseen).'''
        pass

    def iter_pairs(self) -> Iterator[Tuple[Tuple[str, str], int]]:
        '''Yield ((item_a, item_b), count) for all stored pairs.'''
        pass

    def items(self) -> List[str]:
        '''Return all known item names in ID order.'''
        pass

