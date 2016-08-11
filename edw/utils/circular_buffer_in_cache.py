# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.cache import cache


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


#==============================================================================
# Circular buffer
#==============================================================================
class RingBuffer(object):
    """Ring buffer"""
    BUFFER_SIZE_CACHE_KEY_PATTERN = 'rng_buf::%(key)s::sz'
    BUFFER_INDEX_CACHE_KEY_PATTERN = 'rng_buf::%(key)s::in'
    BUFFER_ELEMENT_CACHE_KEY_PATTERN = 'rng_buf::%(key)s::%(index)d::el'

    BUFFER_CACHE_TIMEOUT = 2592000  # 60*60*24*30, 30 days

    _registry = {}

    @staticmethod
    def factory(key, max_size=100, empty=empty):
        result = RingBuffer._registry.get(key)
        if result is None:
            result = RingBuffer._registry[key] = RingBuffer(key, max_size, empty, True)
        return result

    def __init__(self, key, max_size, empty, from_factory=False):
        assert from_factory, 'use "factory" method, for instance create'
        self.key = key
        self.empty = empty
        self.max_size = max(max_size, self.init_size())
        self.init_index()

    def init_size(self):
        key = RingBuffer.BUFFER_SIZE_CACHE_KEY_PATTERN % {'key': self.key}
        val = cache.get(key, None)
        if val is None:
            val = 0
            cache.set(key, val, self.BUFFER_CACHE_TIMEOUT)
        return val

    @property
    def size(self):
        key = RingBuffer.BUFFER_SIZE_CACHE_KEY_PATTERN % {'key': self.key}
        val = cache.get(key, self.empty)
        if val == self.empty:  # HACK: if cache timeout expire
            val = self.max_size
            cache.set(key, val, self.BUFFER_CACHE_TIMEOUT)
        return val

    @size.setter
    def size(self, val):
        key = RingBuffer.BUFFER_SIZE_CACHE_KEY_PATTERN % {'key': self.key}
        cache.set(key, val, self.BUFFER_CACHE_TIMEOUT)

    def init_index(self):
        key = RingBuffer.BUFFER_INDEX_CACHE_KEY_PATTERN % {'key': self.key}
        val = cache.get(key, None)
        if val is None:
            val = -1
            cache.set(key, val, self.BUFFER_CACHE_TIMEOUT)
        return val

    @property
    def index(self):
        key = RingBuffer.BUFFER_INDEX_CACHE_KEY_PATTERN % {'key': self.key}
        val = cache.get(key)
        return val

    @index.setter
    def index(self, val):
        key = RingBuffer.BUFFER_INDEX_CACHE_KEY_PATTERN % {'key': self.key}
        cache.set(key, val, self.BUFFER_CACHE_TIMEOUT)

    def incr_index(self, val=1):
        key = RingBuffer.BUFFER_INDEX_CACHE_KEY_PATTERN % {'key': self.key}
        try:
            result = cache.incr(key, val)  # HACK: if cache timeout expire
        except ValueError:
            result = self.index = 0
        return result

    def set_element(self, index, val):
        key = RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN % {'key': self.key, 'index': index}
        cache.set(key, val, self.BUFFER_CACHE_TIMEOUT)

    def get_element(self, index):
        key = RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN % {'key': self.key, 'index': index}
        return cache.get(key, self.empty)

    def record(self, val):
        """append an element"""
        index = self.incr_index()
        size = self.size
        if size < self.max_size:
            self.set_element(index, val)
            self.size = index + 1
            return self.empty
        else:
            if index == size:
                index = self.index = 0
            else:
                index = index % size
            old = self.get_element(index)
            self.set_element(index, val)
            return old

    def get_all(self):
        """return a list of all the elements"""
        size = self.size
        if size < self.max_size:
            keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN % {'key': self.key, 'index': i} for i in range(size)]
        else:  # Bugfix for self.index is None
            index = self.index
            index = 0 if index is None else index + 1
            keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN % {'key': self.key, 'index': i} for i in range(index, size)]
            keys.extend([RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN % {'key': self.key, 'index': i} for i in range(index)])
        heap = cache.get_many(keys)
        result = []
        for key in keys:
            element = heap.get(key, empty)
            if element != empty:
                result.append(element)
                del heap[key]
        return result

    def clear(self):
        """clear buffer"""
        size = self.size
        keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN % {'key': self.key, 'index': i} for i in range(size)]
        cache.delete_many(keys)
        self.index = -1
        self.size = 0
