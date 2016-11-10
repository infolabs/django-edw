# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from django.conf import settings
from django.utils import formats
from django.utils.dateformat import format, time_format

from datetime import datetime

from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument

from edw.rest.templatetags import BaseRetrieveDataTag
from edw.models.entity import EntityModel
from edw.rest.serializers.entity import (
    # EntityTotalSummarySerializer,
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