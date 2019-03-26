# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from collections import OrderedDict

from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from edw import settings as edw_settings
from edw.utils.hash_helpers import get_cookie_setting


class EDWLimitOffsetPagination(LimitOffsetPagination):

    limit_query_param = 'limit'
    offset_query_param = 'offset'

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.count),
            ('limit', self.limit),
            ('offset', self.offset),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class DataMartPagination(EDWLimitOffsetPagination):
    default_limit = edw_settings.REST_PAGINATION['data_mart_default_limit']
    max_limit = edw_settings.REST_PAGINATION['data_mart_max_limit']


class TermPagination(EDWLimitOffsetPagination):
    default_limit = edw_settings.REST_PAGINATION['term_default_limit']
    max_limit = edw_settings.REST_PAGINATION['term_max_limit']


class EntityPagination(EDWLimitOffsetPagination):
    default_limit = edw_settings.REST_PAGINATION['entity_default_limit']
    max_limit = edw_settings.REST_PAGINATION['entity_max_limit']

    def get_limit(self, request):
        limit = get_cookie_setting(request, "limit")
        return int(limit) if limit else super(EntityPagination, self).get_limit(request)
