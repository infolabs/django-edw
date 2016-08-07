# -*- coding: utf-8 -*-
from django import template
from django.core.urlresolvers import reverse

from classytags.core import Options, Tag
from classytags.arguments import Argument, MultiKeywordArgument

register = template.Library()


#==============================================================================
# List & dict utils
#==============================================================================
@register.filter
def get_value(data, key):
    return data[key]


@register.filter
def pop_value(data, key):
    value = data[key]
    del data[key]
    return value


@register.filter
def append_value(data, value):
    data.append(value)
    return data


@register.filter
def make_dict(value):
    i = iter(value)
    return dict(zip(i, i))


@register.filter
def to_list(value):
    return list(value)


#==============================================================================
# Pass
#==============================================================================
@register.filter
def empty_str(value):
    return ''


#==============================================================================
# String utils
#==============================================================================
@register.filter
def split(string, sep):
    """Return the string split by sep.

    Example usage: {{ value|split:"/" }}
    """
    return string.split(sep)


#==============================================================================
# Objects utils
#==============================================================================
@register.filter
def select_attr(obj, name):
    return {'object': obj, 'name': name}


@register.filter
def set_attr(attribute, value):
    setattr(attribute['object'], attribute['name'], value)
    return attribute['object']


@register.filter
def select_value(obj, key):
    return {'object': obj, 'key': key}


@register.filter
def set_value(data, value):
    data['object'][data['key']] = value
    return data['object']


@register.filter
def select_method(obj, name):
    return {'object': obj, 'name': name}


@register.filter
def call_method_with_arg(method, value):
    return getattr(method['object'], method['name'])(value)


#==============================================================================
# Arithmetic operations
#==============================================================================
@register.filter
def mul(value, arg):
    return value * arg


@register.filter
def div(value, arg):
    return value / arg


@register.filter
def sub(value, arg):
    return value - arg


#==============================================================================
# URL
#==============================================================================
class Url_by_not_empty_kwargs(Tag):
    """
    Returns an absolute path reference (a URL without the domain name) matching a given view function and optional parameters.
    Оnly not empty parameters are considered.
    """

    options = Options(
        Argument('viewname', resolve=True),
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, viewname, kwargs, varname):
        not_empty_kwargs = {}
        for key, value in kwargs.items():
            if bool(value):
                not_empty_kwargs[key] = value
        output = reverse(viewname, kwargs=not_empty_kwargs)
        if varname:
            context[varname] = output
            return ''
        else:
            return output

register.tag(Url_by_not_empty_kwargs)