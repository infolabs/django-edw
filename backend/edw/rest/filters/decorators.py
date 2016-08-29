# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from rest_framework.exceptions import ValidationError


class empty:
    """
    This class is used to represent no data being provided for a given input
    or output value.

    It is required because `None` may be a valid input or output value.
    """
    pass


def get_from_underscore_or_data(var_name, default, from_datadict=empty):
    def get_from_underscore_or_data_decorator(func):
        @wraps(func)
        def func_wrapper(self):
            value = getattr(self, "_{}".format(func.__name__), empty)
            if value == empty:
                value = self.data.get(var_name, empty)
                if value == empty:  # all sources are empty
                    return default
                else:
                    if from_datadict != empty:
                        value = from_datadict(value)
            try:
                result = func(self, value)
            except ValidationError:
                result = default
            return result
        return func_wrapper
    return get_from_underscore_or_data_decorator

