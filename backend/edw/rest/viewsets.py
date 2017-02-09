# -*- coding: utf-8 -*-

from functools import wraps


def remove_empty_params_from_request(exclude=None):
    """
    Remove empty query params from request
    """
    if exclude is None:
        exclude = []
    def remove_empty_params_from_request_decorator(func):
        @wraps(func)
        def func_wrapper(self, request, *args, **kwargs):
            query_params = request.GET.copy()
            for k, v in query_params.items():
                if v == '' and k not in exclude:
                    del query_params[k]
            request.GET = query_params
            return func(self, request, *args, **kwargs)
        return func_wrapper
    return remove_empty_params_from_request_decorator


class CustomSerializerViewSetMixin(object):
    def get_serializer_class(self):
        """ Return the class to use for serializer w.r.t to the request method."""
        try:
            return self.custom_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CustomSerializerViewSetMixin, self).get_serializer_class()
