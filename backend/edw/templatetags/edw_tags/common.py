# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, date as datetime_date

from django.conf import settings
from django.utils import formats
from django.utils.dateformat import time_format
from django.utils.dateformat import format as date_format

from edw.utils.set_helpers import uniq as _uniq


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
    if not (isinstance(value, datetime) or isinstance(value, datetime_date)):
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


def zip_lists(lists):
    for item in zip(*lists):
        yield item


def flatten(data):
    '''
    Flattens a nested array, the array will only be flattened a single level.
    :param data:
    :return:
    '''
    return tuple(j for i in data for j in (i if isinstance(i, (tuple, list)) else (i,)))


def union(data):
    '''
    Computes the union of the passed-in arrays: the list of unique items, in order,
    that are present in one or more of the arrays
    :param data:
    :return:
    '''
    return _uniq(flatten(data))


def uniq(data):
    '''
    Produces a duplicate-free version of the array, using === to test object equality.
    In particular only the first occurrence of each value is kept.
    :param data:
    :return:
    '''
    return _uniq(data)


def intersection(value, arg):
    '''
    Produces a duplicate-free version of the array, using === to test object equality.
    In particular only the first occurrence of each value is kept.
    :param data:
    :return:
    '''
    print(value, arg, list(set(value) & set(arg)))
    return list(set(value) & set(arg))


def append_value(data, value):
    data.append(value)
    return data


def empty_str(value):
    return ''


def multiply(value, arg):
    return value * arg


def divide(value, arg):
    return value / arg


def minimal(value, arg):
    return min(value, arg)


def maximal(value, arg):
    return max(value, arg)


def bitwise_and(value, arg):
    return bool(value & arg)


def select_attr(obj, name):
    """Prepares data for set_attr"""
    return {'object': obj, 'name': name}


def set_attr(attribute, value):
    """{{ request|select_attr:'foobar'|set_attr:42 }} """
    setattr(attribute['object'], attribute['name'], value)
    return attribute['object']


def select_value(obj, key):
    """Prepares data for set_value"""
    return {'object': obj, 'key': key}


def set_value(data, value):
    """{{ request|select_value:'foobar'|set_value:42 }} """
    data['object'][data['key']] = value
    return data['object']
