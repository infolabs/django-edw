# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.utils import six
from django.template import Context, RequestContext, Template


class obj(object):
    def __init__(self, dict_):
        self.__dict__.update(dict_)


def dict2obj(d):
    return json.loads(json.dumps(d), object_hook=obj)


class classproperty(object):
    """Like @property, but for classes, not just instances.
    Example usage:
        >>> from cms.utils.helpers import classproperty
        >>> class A(object):
        ...     @classproperty
        ...     def x(cls):
        ...         return 'x'
        ...     @property
        ...     def y(self):
        ...         return 'y'
        ...
        >>> A.x
        'x'
        >>> A().x
        'x'
        >>> A.y
        <property object at 0x2939628>
        >>> A().y
        'y'
    """
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def unicode_to_repr(value):
    # Coerce a unicode string to the correct repr return type, depending on
    # the Python version. We wrap all our `__repr__` implementations with
    # this and then use unicode throughout internally.
    if six.PY2:
        return value.encode('utf-8')
    return value


def template_render(template, context=None, request=None):
    """
    Passing Context or RequestContext to Template.render is deprecated in 1.9+,
    see https://github.com/django/django/pull/3883 and
    https://github.com/django/django/blob/1.9/django/template/backends/django.py#L82-L84
    :param template: Template instance
    :param context: dict
    :param request: Request instance
    :return: rendered template as SafeText instance
    """
    if isinstance(template, Template):
        if request:
            context = RequestContext(request, context)
        else:
            context = Context(context)
        return template.render(context)
    # backends template, e.g. django.template.backends.django.Template
    else:
        return template.render(context, request=request)


try:
    from django_filters.rest_framework import backends
except ImportError:
    from rest_framework_filters.backends import DjangoFilterBackend
else:
    from rest_framework_filters.filterset import FilterSet
    from django.template import TemplateDoesNotExist, loader

    class DjangoFilterBackend(backends.DjangoFilterBackend):
        default_filter_set = FilterSet

        def filter_queryset(self, request, queryset, view):
            filter_class = self.get_filter_class(view, queryset)

            if filter_class:
                if hasattr(filter_class, 'get_subset'):
                    filter_class = filter_class.get_subset(request.query_params)
                return filter_class(request.query_params, queryset=queryset).qs

            return queryset

        def to_html(self, request, queryset, view):
            filter_class = self.get_filter_class(view, queryset)
            if not filter_class:
                return None
            filter_instance = filter_class(request.query_params, queryset=queryset)

            # forces `form` evaluation before `qs` is called. This prevents an empty form from being cached.
            filter_instance.form

            try:
                template = loader.get_template(self.template)
            except TemplateDoesNotExist:
                template = Template(backends.template_default)

            return template_render(template, context={
                'filter': filter_instance
            })
