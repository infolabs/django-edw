# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#from collections import OrderedDict
from datetime import datetime
from django import template
from django.conf import settings
#from django.template.loader import select_template
from django.utils import formats
from django.utils.safestring import mark_safe
from django.utils.dateformat import format, time_format
#from classytags.helpers import InclusionTag
#from edw import settings as edw_settings

register = template.Library()


def from_iso8601(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


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

'''
@register.filter
def rest_json(value, arg=None):
    """
    Renders a `ReturnDict` as used by the REST framework into a safe JSON string.
    """
    if not value:
        return mark_safe('{}')
    if not isinstance(value, (dict, OrderedDict, list, tuple)):
        msg = "Given value must be of type dict, OrderedDict, list or tuple but it is {}."
        raise ValueError(msg.format(value.__class__.__name__))
    data = JSONRenderer().render(value)
    return mark_safe(data)
'''

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