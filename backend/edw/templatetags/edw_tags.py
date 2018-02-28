# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from functools import reduce

from django import template

from django.conf import settings
from django.utils import formats
from django.utils.dateformat import format, time_format

try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text

from datetime import datetime

from classytags.core import Tag
from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument

from rest_framework_filters.backends import DjangoFilterBackend

from rest_framework import filters

from edw.rest.pagination import EntityPagination, DataMartPagination
from edw.rest.templatetags import BaseRetrieveDataTag
from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.rest.filters.entity import (
    EntityFilter,
    EntityMetaFilter,
    EntityDynamicFilter,
    EntityOrderingFilter
)
from edw.rest.filters.data_mart import DataMartFilter
from edw.rest.serializers.entity import (
    EntityTotalSummarySerializer,
    EntityDetailSerializer
)
from edw.rest.serializers.data_mart import (
    DataMartSummarySerializer,
    DataMartDetailSerializer
)

register = template.Library()


def from_iso8601(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


#==============================================================================
# Common
#==============================================================================
@register.filter(expects_localtime=True, is_safe=False)
def date(value, arg=None):
    """
    Alternative implementation to the built-in `date` template filter which also accepts the
    date string in iso-8601 as passed in by the REST serializers.
    """
    if value in (None, ''):
        return ''
    if not isinstance(value, datetime):
        value = from_iso8601(value)
    if arg is None:
        arg = settings.DATE_FORMAT
    try:
        return formats.date_format(value, arg)
    except AttributeError:
        try:
            return format(value, arg)
        except AttributeError:
            return ''


@register.filter(expects_localtime=True, is_safe=False)
def time(value, arg=None):
    """
    Alternative implementation to the built-in `time` template filter which also accepts the
    date string in iso-8601 as passed in by the REST serializers.
    """
    if value in (None, ''):
        return ''
    if not isinstance(value, datetime):
        value = from_iso8601(value)
    if arg is None:
        arg = settings.TIME_FORMAT
    try:
        return formats.time_format(value, arg)
    except AttributeError:
        try:
            return time_format(value, arg)
        except AttributeError:
            return ''


#==============================================================================
# String utils
#==============================================================================
@register.filter
def split(value, separator):
    """Return the string split by separator.

    Example usage: {{ value|split:"/" }}
    """
    return value.split(separator)


@register.filter
def trim(value):
    """Removes whitespaces around the string.

    Example usage: {{ value|trim }}
    """
    return value.strip()


#==============================================================================
# Math utils
#==============================================================================
@register.filter
def multiply(value, arg):
    return value * arg


#==============================================================================
# Logical utils
#==============================================================================
@register.filter
def bitwise_and(value, arg):
    return bool(value & arg)


#==============================================================================
# Entities utils
#==============================================================================
class GetEntity(BaseRetrieveDataTag):
    name = 'get_entity'
    queryset = EntityModel.objects.all()
    serializer_class = EntityDetailSerializer
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

register.tag(GetEntity)


class GetEntities(BaseRetrieveDataTag):
    name = 'get_entities'
    queryset = EntityModel.objects.all()
    serializer_class = EntityTotalSummarySerializer
    action = 'list'

    filter_class = EntityFilter
    filter_backends = (DjangoFilterBackend, EntityMetaFilter, EntityDynamicFilter, EntityOrderingFilter)
    ordering_fields = '__all__'

    pagination_class = EntityPagination

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

    def get_serializer_context(self):
        context = super(GetEntities, self).get_serializer_context()
        context.update(self.queryset_context)
        return context

    def filter_queryset(self, queryset):
        queryset = super(GetEntities, self).filter_queryset(queryset)
        query_params = self.request.GET

        data_mart = query_params['_data_mart']
        if data_mart is not None:
            query_params.setdefault(self.paginator.limit_query_param, str(data_mart.limit))

        self.queryset_context = {
            "extra": None,
            "initial_filter_meta": query_params['_initial_filter_meta'],
            "initial_queryset": query_params['_initial_queryset'],
            "terms_filter_meta": query_params['_terms_filter_meta'],
            "data_mart": data_mart,
            "terms_ids": query_params['_terms_ids'],
            "subj_ids": query_params['_subj_ids'],
            "ordering": query_params['_ordering'],
            "view_component": query_params['_view_component'],
            "annotation_meta": query_params['_annotation_meta'],
            "aggregation_meta": query_params['_aggregation_meta'],
            "filter_queryset": queryset
        }
        return queryset

register.tag(GetEntities)


@register.filter
def attributes_has_view_class(value, arg):
    if value and isinstance(value, (tuple, list)):
        getter = (lambda x: x['view_class']) if isinstance(value[0], dict) else lambda x: x.view_class
        for attr in value:
            view_class = getter(attr)
            if arg in view_class:
                return True
    return False


#==============================================================================
# DataMarts utils
#==============================================================================
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

register.tag(GetDataMart)


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

    # def get_serializer_context(self):
    #     context = super(GetDataMarts, self).get_serializer_context()
    #     # context.update(self.queryset_context)
    #     return context

    # def filter_queryset(self, queryset):
    #     queryset = super(GetDataMarts, self).filter_queryset(queryset)
    #     # query_params = self.request.GET
    #     #
    #     # self.queryset_context = {
    #     #     "initial_queryset": query_params['_initial_queryset'],
    #     #     "filter_queryset": queryset
    #     # }
    #     return queryset

register.tag(GetDataMarts)


#==============================================================================
# Frontend utils
#==============================================================================

class CompactJson(Tag):
    name = 'compactjson'

    options = Options(
        'as',
        Argument('varname', required=False, resolve=False),
        blocks=[('endcompactjson', 'nodelist')]
    )

    def render_tag(self, context, nodelist, varname):
        block_data = reduce(
            lambda x, y: x + smart_text(y),
            map(
                lambda x: x.render(context),
                nodelist
            )
        )
        block_data = json.loads(block_data)
        block_data = json.dumps(block_data)
        if varname:
            context[varname] = block_data
            return ''
        else:
            return block_data

register.tag(CompactJson)

