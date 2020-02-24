# -*- coding: utf-8 -*-

from functools import wraps


def remove_empty_params_from_request(exclude=None):
    """
    ENG: Remove empty query params from request
    RUS: Удаляет пустые параметры из запроса
    """
    if exclude is None:
        exclude = []

    def remove_empty_params_from_request_decorator(func):
        """
         RUS: Удаляет пустые параметры из запроса в результате применения декоратора
        """
        @wraps(func)
        def func_wrapper(self, request, *args, **kwargs):
            """
            Функция-обертка
            """
            query_params = request.GET.copy()
            for k, v in list(query_params.items()):
                if v == '' and k not in exclude:
                    del query_params[k]
            request.GET = query_params
            return func(self, request, *args, **kwargs)
        return func_wrapper
    return remove_empty_params_from_request_decorator


class CustomSerializerViewSetMixin(object):
    """
    Сериалайзер для запросов
    """
    def get_serializer_class(self):
        """
        ENG: Return the class to use for serializer w.r.t to the request method.
        RUS: Возвращает класс для использования сериалайзера к методу запроса
        """
        try:
            return self.custom_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(CustomSerializerViewSetMixin, self).get_serializer_class()
