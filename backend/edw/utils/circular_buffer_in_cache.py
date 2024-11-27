# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.cache import cache
from django.utils.functional import cached_property


class empty:
    """

    Class empty

    This is a placeholder class that does not contain any specific logic or functionality.
    This is particularly useful for distinguishing between a None value (which may be a valid value in some contexts) and a lack of data.

    Methods:
        None

    Attributes:
        None

    """
    pass


#==============================================================================
# Circular buffer
#==============================================================================
class RingBuffer(object):
    """RingBuffer class represents a circular buffer that stores a fixed number of elements.
        The buffer is implemented using a cache storage.

    Attributes:
        BUFFER_SIZE_CACHE_KEY_PATTERN (str): The pattern used to generate the cache key for storing the buffer size.
        BUFFER_INDEX_CACHE_KEY_PATTERN (str): The pattern used to generate the cache key for storing the buffer index.
        BUFFER_ELEMENT_CACHE_KEY_PATTERN (str): The pattern used to generate the cache key for storing buffer elements.
        BUFFER_CACHE_TIMEOUT (int): The timeout for cache entries, in seconds.
        _registry (dict): A dictionary used to store instances of the RingBuffer class.

    Methods:
        factory(key, max_size=100, empty=None)
        __init__(self, key, max_size, empty, from_factory=False)
        init_size()
        size()
        size(val)
        init_index()
        index()
        index(val)
        incr_index(val=1)
        set_element(index, val)
        get_element(index)
        record(val)
        get_all()
        clear()
    """
    BUFFER_SIZE_CACHE_KEY_PATTERN = 'rng_buf:{key}:sz'
    BUFFER_INDEX_CACHE_KEY_PATTERN = 'rng_buf:{key}:in'
    BUFFER_ELEMENT_CACHE_KEY_PATTERN = 'rng_buf:{key}:{index}:el'

    DEFAULT_BUFFER_CACHE_TIMEOUT = 2592000  # 60*60*24*30, 30 days

    _registry = {}

    @staticmethod
    def factory(key, max_size=100, empty=empty, timeout=None):
        result = RingBuffer._registry.get(key, None)
        if result is None:
            result = RingBuffer._registry[key] = RingBuffer(key, max_size, empty, True, timeout)
        return result

    def __init__(self, key, max_size, empty, from_factory=False, timeout=None):
        assert from_factory, 'use "factory" method, for instance create'
        self.key = key
        self.empty = empty
        self.timeout = timeout if timeout else self.DEFAULT_BUFFER_CACHE_TIMEOUT
        self.max_size = max(max_size, self.init_size())
        self.init_index()

    @cached_property
    def buffer_size_cache_key(self):
        return RingBuffer.BUFFER_SIZE_CACHE_KEY_PATTERN.format(key=self.key)

    @cached_property
    def buffer_index_cache_key(self):
        return RingBuffer.BUFFER_INDEX_CACHE_KEY_PATTERN.format(key=self.key)

    def init_size(self):
        val = cache.get(self.buffer_size_cache_key, None)
        if val is None:
            val = 0
            cache.set(self.buffer_size_cache_key, val, self.timeout)
        return val

    @property
    def size(self):
        val = cache.get(self.buffer_size_cache_key, None)
        if val is None:  # HACK: if cache timeout expire
            val = self.max_size
            cache.set(self.buffer_size_cache_key, val, self.timeout)
        return val

    @size.setter
    def size(self, val):
        cache.set(self.buffer_size_cache_key, val, self.timeout)

    def init_index(self):
        val = cache.get(self.buffer_index_cache_key, None)
        if val is None:
            val = -1
            cache.set(self.buffer_index_cache_key, val, self.timeout)
        return val

    @property
    def index(self):
        return cache.get(self.buffer_index_cache_key, None)

    @index.setter
    def index(self, val):
        cache.set(self.buffer_index_cache_key, val, self.timeout)

    def incr_index(self, val=1):
        try:
            result = cache.incr(self.buffer_index_cache_key, val)  # HACK: if cache timeout expire
        except ValueError:
            result = self.index = 0
        return result

    def set_element(self, index, val):
        key = RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=index)
        cache.set(key, val, self.timeout)

    def get_element(self, index):
        key = RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=index)
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
            keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=i) for i in range(size)]
        else:  # Bugfix for self.index is None
            index = self.index
            index = 0 if index is None else index + 1
            keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=i) for i in range(index, size)]
            keys.extend([RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=i) for i in range(index)])
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
        keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=i) for i in range(size)]
        cache.delete_many(keys)
        self.index = -1
        self.size = 0
