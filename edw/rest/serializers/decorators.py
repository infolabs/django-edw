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


def get_from_context_or_request(var_name, default):
    def get_from_context_or_request_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            result = self.context.get(var_name, empty)
            if result == empty:
                if hasattr(default, '__call__'):
                    if hasattr(self, default.__name__):
                        result = default(self)
                    else:
                        result = default()
                else:
                    result = default
                request = self.context.get('request')
                if request:
                    value = request.GET.get(var_name, empty)
                    if value != empty:
                        result = func(self, value)
                self.context[var_name] = result
            return result
        return func_wrapper
    return get_from_context_or_request_decorator


