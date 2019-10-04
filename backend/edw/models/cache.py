# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.core.cache import cache

from edw.utils.hash_helpers import create_hash

DEFAULT_CACHE_KEY_ATTR = '_cache_key'
DEFAULT_CACHE_TIMEOUT = 300  # 5 minutes


class empty:
    """
    ENG: This class is used to represent no data being provided for a given input
    or output value.
    It is required because `None` may be a valid input or output value.
    RUS: Используется для представления данных, не содержащихся в данном входном или выходном значении.
    """
    pass


def _parse_cache_key(self, cache_key, *args, **kwargs):
    """
    RUS: Возвращает ключ кэша, если в ключе содержится метод '__call__', то ключ кэша может быть переопределен.
    """
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
                  trim_key_pattern='{model}:~{hash}',
                  key_max_len=50,
                  **dkwargs):
    """
    RUS: Добавляет ключ кэша с определенными параметрами.
    """
    def add_cache_key_decorator(func):
        """
        RUS: Создает декоратор ключа кэша. Если длина ключа больше его максимальной длины, то ключ обрезается.
        """
        @wraps(func)
        def func_wrapper(self, *args, **kwargs):
            cache_key_attr = dkwargs.get('cache_key_attr', getattr(self, '_cache_key_attr', DEFAULT_CACHE_KEY_ATTR))
            result = func(self, *args, **kwargs)
            setattr(result, '_cache_key_attr', cache_key_attr)
            model_class = result.model if hasattr(result, 'model') else (
                self.model if hasattr(self, 'model') else self.__class__
            )
            key = contact_key_pattern.format(**{
                'prev': getattr(self, cache_key_attr),
                'next': _parse_cache_key(self, cache_key, *args, **kwargs)
            }) if hasattr(self, cache_key_attr) else new_key_pattern.format(**{
                'new': _parse_cache_key(self, cache_key, *args, **kwargs),
                'model': model_class._meta.object_name.lower()
            })
            if len(key) > key_max_len:
                key = trim_key_pattern.format(**{
                    'hash': create_hash(key),
                    'model': model_class._meta.object_name.lower()
                })
            setattr(result, cache_key_attr, key)
            return result
        return func_wrapper
    return add_cache_key_decorator


class QuerySetCachedResultMixin(object):
    """
    ENG: Try find result in cache, otherwise calculate it.
    RUS: Пытается найти результат кэширования или вычислить его.
    """

    @staticmethod
    def prepare_for_cache(data):
        return _ReadyForCache(data)

    def _get_from_global_cache(self, key, on_cache_set, timeout):
        """
        RUS: Получает результат кэширования по ключу из глобального кэша.
        """
        result = cache.get(key, empty)
        if result == empty:
            result = self.prepare_for_cache(self)
            cache.set(key, result, timeout)
            if on_cache_set is not None:
                on_cache_set(key)

        return result

    def cache(self,
              on_cache_set=None,
              timeout=DEFAULT_CACHE_TIMEOUT,
              local_cache=None):
        """
        RUS: Возвращает результат кэширования по ключу из локального кэша, если пустой результат,
        то ключ локального кэша создаетсяиз глобального.
        Если ключ пустой, возбуждается исключение.
        """
        cache_key_attr = getattr(self, '_cache_key_attr', DEFAULT_CACHE_KEY_ATTR)
        key = getattr(self, cache_key_attr, empty)
        if key != empty:
            if local_cache is not None:
                result = local_cache.get(key, empty)
                if result == empty:
                    result = self._get_from_global_cache(key, on_cache_set, timeout)
                    local_cache[key] = result
                # создаем поверхностную копию чтобы минимизировать возможность "затереть" кеш
                result = result[:]
            else:
                result = self._get_from_global_cache(key, on_cache_set, timeout)
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
        """
        RUS: Извлекает атрибут ключа кэша, если он не пустой, извлекается ключ, если он не пустой,
        ключ кэша переопределяется.
        """
        cache_key_attr = getattr(data, '_cache_key_attr', empty)
        if cache_key_attr != empty:
            cache_key = getattr(data, cache_key_attr, empty)
            if cache_key != empty:
                setattr(self, cache_key_attr, cache_key)
        super(_ReadyForCache, self).__init__(data)
