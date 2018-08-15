# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import filters
from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument
from rest_framework_filters.backends import DjangoFilterBackend

from edw.models.data_mart import DataMartModel
from edw.rest.pagination import DataMartPagination
from edw.rest.templatetags import BaseRetrieveDataTag
from edw.rest.filters.data_mart import DataMartFilter
from edw.rest.serializers.data_mart import (
    DataMartSummarySerializer,
    DataMartDetailSerializer,
)


class GetDataMart(BaseRetrieveDataTag):
    name = 'get_data_mart'
    queryset = DataMartModel.objects.all()
    serializer_class = DataMartDetailSerializer
    action = 'retrieve'

    options = Options(
        Argument('pk', resolve=True),
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, pk, kwargs, varname):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if varname:
            context[varname] = data
            return ''
        else:
            return self.to_json(data)


class GetDataMarts(BaseRetrieveDataTag):
    name = 'get_data_marts'
    queryset = DataMartModel.objects.all()
    serializer_class = DataMartSummarySerializer
    action = 'list'

    filter_class = DataMartFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter)
    ordering_fields = '__all__'

    pagination_class = DataMartPagination

    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, kwargs, varname):

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_data(serializer.data)
            context["{}_paginator".format(varname)] = self.paginator
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

        if varname:
            context[varname] = data
            return ''
        else:
            return self.to_json(data)
