# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.core.cache import cache


DEFAULT_CACHE_KEY_ATTR = '_cache_key'
DEFAULT_CACHE_TIMEOUT = 300  # 5 minutes


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


def _parse_cache_key(self, cache_key, *args, **kwargs):
    if hasattr(cache_key, '__call__'):
        if hasattr(self, cache_key.__name__):
            return cache_key(self, *args, **kwargs)
        else:
            return cache_key(*args, **kwargs)
    else:
        return cache_key


def add_cache_key(cache_key,
                  contact_key_pattern='{prev}:{next}',
                  new_key_pattern='{model}:{new}',
                  **dkwargs):
    def add_cache_key_decorator(func):
        @wraps(func)
        def func_wrapper(self, *args, **kwargs):
            cache_key_attr = dkwargs.get('cache_key_attr', getattr(self, '_cache_key_attr', DEFAULT_CACHE_KEY_ATTR))
            result = func(self, *args, **kwargs)
            setattr(result, '_cache_key_attr', cache_key_attr)

            if hasattr(self, cache_key_attr):
                setattr(result, cache_key_attr, contact_key_pattern.format(**{
                    'prev': getattr(self, cache_key_attr),
                    'next': _parse_cache_key(self, cache_key, *args, **kwargs)
                }))
            else:
                model_class = result.model if hasattr(result, 'model') else (
                    self.model if hasattr(self, 'model') else self.__class__
                )

                setattr(result, cache_key_attr, new_key_pattern.format(**{
                    'new':_parse_cache_key(self, cache_key, *args, **kwargs),
                    'model': model_class._meta.object_name.lower()
                }))
            return result
        return func_wrapper
    return add_cache_key_decorator


class QuerySetCachedResultMixin(object):
    '''
    Try find result in cache, otherwise calculate it
    '''
    @staticmethod
    def prepare_for_cache(data):
        return _ReadyForCache(data)

    def cache(self,
              on_cache_set=None,
              timeout=DEFAULT_CACHE_TIMEOUT):
        cache_key_attr = getattr(self, '_cache_key_attr', DEFAULT_CACHE_KEY_ATTR)
        key = getattr(self, cache_key_attr, empty)
        if key != empty:
            result = cache.get(key, empty)
            if result == empty:
                result = self.prepare_for_cache(self)
                cache.set(key, result, timeout)
                if on_cache_set is not None:
                    on_cache_set(key)
        else:
            raise AttributeError(
                '{cls}.{attr} not found.'.format(
                    cls=self.__class__.__name__,
                    attr=cache_key_attr
                )
            )
        return result


class _ReadyForCache(QuerySetCachedResultMixin, list):

    def __init__(self, data):
        cache_key_attr = getattr(data, '_cache_key_attr', empty)
        if cache_key_attr != empty:
            cache_key = getattr(data, cache_key_attr, empty)
            if cache_key != empty:
                setattr(self, cache_key_attr, cache_key)

        super(_ReadyForCache, self).__init__(data)

