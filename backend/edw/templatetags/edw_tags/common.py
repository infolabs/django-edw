# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.conf import settings
from django.utils import formats
from django.utils.dateformat import time_format
from django.utils.dateformat import format as date_format


def from_iso8601(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


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
            return date_format(value, arg)
        except AttributeError:
            return ''


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


def split(value, separator):
    """Return the string split by separator.

    Example usage: {{ value|split:"/" }}
    """
    return value.split(separator)


def trim(value):
    """Removes whitespaces around the string.

    Example usage: {{ value|trim }}
    """
    return value.strip()


def to_list(value):
    return list(value)


def append_value(data, value):
    data.append(value)
    return data


def empty_str(value):
    return ''


def multiply(value, arg):
    return value * arg


def bitwise_and(value, arg):
    return bool(value & arg)
