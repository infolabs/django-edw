# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps


def get_from_context_or_request(var_name, default):
    def get_from_context_or_request_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            result = self.context.get(var_name)
            if result is None:
                result = default
                request = self.context.get('request')
                if request:
                    value = request.GET.get(var_name)
                    if not value is None:
                        result = func(self, value)
                self.context[var_name] = result
            return result
        return func_wrapper
    return get_from_context_or_request_decorator
