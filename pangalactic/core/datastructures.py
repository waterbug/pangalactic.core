# -*- coding: utf-8 -*-
"""
Structures for data.
"""
from collections.abc import MutableSet


def chunkify(data, chunk_size):
    """
    Return the specified data (a list) as a list of lists each of length
    'chunk_size' plus a final list containing the remainder (if any).  If the
    length of the data is <= chunk size, return a list containing the data
    list.

    Args:
        data (iterable):  the data to be returned in chunks
        chunk_size (int):  length of each chunk
    """
    if len(data) <= chunk_size:
        return [data]
    full_chunks = len(data) // chunk_size
    chunks = [data[i*chunk_size : (i + 1)*chunk_size]
              for i in range(0, full_chunks)]
    if (len(data) % chunk_size):
        chunks.append(data[chunk_size * full_chunks :])
    return chunks


class OrderedSet(MutableSet):
    """
    Set that remembers original insertion order.

    (Recipe from http://code.activestate.com/recipes/576694/
    in ActiveState cookbook.)
    """

    def __init__(self, iterable=None):
        self.end = end = [] 
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:        
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

