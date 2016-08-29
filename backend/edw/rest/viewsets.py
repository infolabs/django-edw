# -*- coding: utf-8 -*-

from functools import wraps


def remove_empty_params_from_request(func):
    """
    Remove empty query params from request
    """
    @wraps(func)
    def func_wrapper(self, request, *args, **kwargs):
        query_params = request.GET.copy()
        for k, v in query_params.items():
            if v == '':
                del query_params[k]
        request.GET = query_params
        return func(self, request, *args, **kwargs)
    return func_wrapper


class CustomSerializerViewSetMixin(object):
    def get_serializer_class(self):
        """ Return the class to use for serializer w.r.t to the request method."""
        try:
            return self.custom_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CustomSerializerViewSetMixin, self).get_serializer_class()
