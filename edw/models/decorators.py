# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


def _parse_cache_key(self, cache_key):
    if hasattr(cache_key, '__call__'):
        if hasattr(self, cache_key.__name__):
            return cache_key(self)
        else:
            return cache_key()
    else:
        return cache_key


DEFAULT_CACHE_KEY_ATTR = '_cache_key'


def add_cache_key(cache_key,
                  cache_key_attr=DEFAULT_CACHE_KEY_ATTR,
                  contact_key_pattern='{prev}:{next}',
                  new_key_pattern='{new}'):
    def add_cache_key_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            result = func(self)
            if hasattr(self, cache_key_attr):
                setattr(result, cache_key_attr, contact_key_pattern.format(**{
                    'prev': getattr(self, cache_key_attr),
                    'next': _parse_cache_key(self, cache_key)
                }))
            else:
                setattr(result, cache_key_attr, new_key_pattern.format(
                    new=_parse_cache_key(self, cache_key)
                ))
            return result
        return func_wrapper
    return add_cache_key_decorator


class QuerySetCachedResultMixin(object):
    '''
    Try find result in cache, otherwise calculate it
    '''
    def from_cache(self, callback=None, cache_key_attr=DEFAULT_CACHE_KEY_ATTR):
        if not hasattr(self, cache_key_attr):
            raise AttributeError(
                '{cls}.{attr} not found.'.format(
                    cls=self.__class__.__name__,
                    attr=cache_key_attr
                )
            )
        else:
            print "Try from cache!!!"
        return None