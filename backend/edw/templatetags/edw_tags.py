# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from django.conf import settings
from django.utils import formats
from django.utils.dateformat import format, time_format

from datetime import datetime

from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.pagination import EntityPagination
from edw.rest.templatetags import BaseRetrieveDataTag
from edw.models.entity import EntityModel
from edw.rest.filters.entity import EntityFilter, EntityMetaFilter, EntityOrderingFilter
from edw.rest.serializers.entity import (
    EntityTotalSummarySerializer,
    EntityDetailSerializer
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

    filter_class = EntityFilter
    filter_backends = (DjangoFilterBackend, EntityMetaFilter, EntityOrderingFilter)
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
            "subj_ids": query_params['_subj_ids'],
            "ordering": query_params['_ordering'],
            "view_component": query_params['_view_component'],
            "filter_queryset": queryset
        }
        return queryset

register.tag(GetEntities)
