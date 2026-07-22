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
        """Return a shared ``RingBuffer`` for ``key`` (creates it once).

        Instances are memoized in ``RingBuffer._registry`` per ``key`` so all
        callers share the same buffer state.

        Args:
            key (str): unique buffer name (part of the cache keys).
            max_size (int): maximum number of stored elements.
            empty: sentinel returned when a slot has no value.
            timeout (int | None): cache TTL for buffer keys; defaults to
                ``DEFAULT_BUFFER_CACHE_TIMEOUT`` (30 days).

        Returns:
            RingBuffer: shared instance for ``key``.
        """
        result = RingBuffer._registry.get(key, None)
        if result is None:
            result = RingBuffer._registry[key] = RingBuffer(key, max_size, empty, True, timeout)
        return result

    def __init__(self, key, max_size, empty, from_factory=False, timeout=None):
        """Initialize buffer state; prefer :meth:`factory` over direct call.

        Args:
            key (str): unique buffer name.
            max_size (int): maximum number of stored elements.
            empty: sentinel for empty slots.
            from_factory (bool): must be ``True`` (guards direct instantiation).
            timeout (int | None): cache TTL for buffer keys.

        Raises:
            AssertionError: if not created via :meth:`factory`.
        """
        assert from_factory, 'use "factory" method, for instance create'
        self.key = key
        self.empty = empty
        self.timeout = timeout if timeout else self.DEFAULT_BUFFER_CACHE_TIMEOUT
        self.max_size = max(max_size, self.init_size())
        self.init_index()

    @cached_property
    def buffer_size_cache_key(self):
        """str: cache key that stores the current buffer size."""
        return RingBuffer.BUFFER_SIZE_CACHE_KEY_PATTERN.format(key=self.key)

    @cached_property
    def buffer_index_cache_key(self):
        """str: cache key that stores the current write index."""
        return RingBuffer.BUFFER_INDEX_CACHE_KEY_PATTERN.format(key=self.key)

    def init_size(self):
        """Read current size from cache, initializing it to ``0`` if absent.

        Returns:
            int: current number of stored elements.
        """
        val = cache.get(self.buffer_size_cache_key, None)
        if val is None:
            val = 0
            cache.set(self.buffer_size_cache_key, val, self.timeout)
        return val

    @property
    def size(self):
        """int: current buffer size (restored to ``max_size`` if the key expired)."""
        val = cache.get(self.buffer_size_cache_key, None)
        if val is None:  # HACK: if cache timeout expire
            val = self.max_size
            cache.set(self.buffer_size_cache_key, val, self.timeout)
        return val

    @size.setter
    def size(self, val):
        """Persist the buffer size ``val`` into cache.

        Args:
            val (int): new buffer size.
        """
        cache.set(self.buffer_size_cache_key, val, self.timeout)

    def init_index(self):
        """Read current write index from cache, initializing it to ``-1`` if absent.

        Returns:
            int: current write index.
        """
        val = cache.get(self.buffer_index_cache_key, None)
        if val is None:
            val = -1
            cache.set(self.buffer_index_cache_key, val, self.timeout)
        return val

    @property
    def index(self):
        """int | None: current write index (``None`` if the key expired)."""
        return cache.get(self.buffer_index_cache_key, None)

    @index.setter
    def index(self, val):
        """Persist the write index ``val`` into cache.

        Args:
            val (int): new write index.
        """
        cache.set(self.buffer_index_cache_key, val, self.timeout)

    def incr_index(self, val=1):
        """Atomically increment the write index (resets to ``0`` if key expired).

        Args:
            val (int): increment step.

        Returns:
            int: the new index value.
        """
        try:
            result = cache.incr(self.buffer_index_cache_key, val)  # HACK: if cache timeout expire
        except ValueError:
            result = self.index = 0
        return result

    def set_element(self, index, val):
        """Store ``val`` in slot ``index``.

        Args:
            index (int): slot position.
            val: value to store.
        """
        key = RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=index)
        cache.set(key, val, self.timeout)

    def get_element(self, index):
        """Return the value stored in slot ``index``.

        Args:
            index (int): slot position.

        Returns:
            The stored value, or ``self.empty`` if the slot is empty.
        """
        key = RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=index)
        return cache.get(key, self.empty)

    def record(self, val):
        """Append ``val`` to the buffer (FIFO overwrite when full).

        Args:
            val: value to append.

        Returns:
            ``self.empty`` while the buffer is not full; otherwise the element
            that was evicted from the overwritten slot (the caller is
            responsible for deleting it from the cache).
        """
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
        """Return all currently stored elements in insertion order.

        Returns:
            list: stored elements (empty slots are skipped).
        """
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
        """Remove all stored elements and reset size/index."""
        size = self.size
        keys = [RingBuffer.BUFFER_ELEMENT_CACHE_KEY_PATTERN.format(key=self.key, index=i) for i in range(size)]
        cache.delete_many(keys)
        self.index = -1
        self.size = 0
