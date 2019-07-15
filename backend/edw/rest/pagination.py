# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from edw import settings as edw_settings
from edw.utils.hash_helpers import get_cookie_setting


class EDWLimitOffsetPagination(LimitOffsetPagination):
    """
    Определяет стиль нумерации страниц, используемый при поиске нескольких записей базы данных
    """

    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def get_paginated_response(self, data):
        """
        ENG: Method is passed the serialized page data and should return a Response instance
        RUS: Передаются сериализованные страницы и возвращает пользвательский стиль нумерации страниц
        """
        return Response(OrderedDict([
            ('count', self.count),
            ('limit', self.limit),
            ('offset', self.offset),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class DataMartPagination(EDWLimitOffsetPagination):
    """
    Определяет стиль нумерации страниц витрины данных
    """
    default_limit = edw_settings.REST_PAGINATION['data_mart_default_limit']
    max_limit = edw_settings.REST_PAGINATION['data_mart_max_limit']


class TermPagination(EDWLimitOffsetPagination):
    """
    Определяет стиль нумерации страниц терминов
    """
    default_limit = edw_settings.REST_PAGINATION['term_default_limit']
    max_limit = edw_settings.REST_PAGINATION['term_max_limit']


class EntityPagination(EDWLimitOffsetPagination):
    """
     Определяет стиль нумерации страниц объекта
    """
    default_limit = edw_settings.REST_PAGINATION['entity_default_limit']
    max_limit = edw_settings.REST_PAGINATION['entity_max_limit']

    def get_limit(self, request):
        """
        Возвращает максимальное количество элементов запроса
        """
        limit = get_cookie_setting(request, "limit")
        return int(limit) if limit else super(EntityPagination, self).get_limit(request)
