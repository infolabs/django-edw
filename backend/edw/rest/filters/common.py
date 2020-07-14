# -*- coding: utf-8 -*-

from django.template import Context, RequestContext, Template

from django_filters.filters import (
    BaseInFilter,
    # BaseRangeFilter,
    NumberFilter,
    # DateTimeFilter,
    Filter
)
from django_filters.fields import BaseCSVField

from edw.rest.filters.widgets import CSVWidget as CustomCSVWidget


class CustomCSVField(BaseCSVField):
    widget = CustomCSVWidget


class NumberInFilter(BaseInFilter, NumberFilter):
    base_field_class = CustomCSVField


# class DateTimeFromToRangeFilter(BaseRangeFilter, DateTimeFilter):
#     pass


class MethodFilter(Filter):
    """
    This filter will allow you to run a method that exists on the filterset class
    """
    def __init__(self, *args, **kwargs):
        self.action = kwargs.pop('action', '')
        super(MethodFilter, self).__init__(*args, **kwargs)

    def resolve_action(self):
        """
        This method provides a hook for the parent FilterSet to resolve the filter's
        action after initialization. This is necessary, as the filter name may change
        as it's expanded across related filtersets.
        ie, `is_published` might become `post__is_published`.
        """
        # noop if a function was provided as the action
        if callable(self.action):
            return

        # otherwise, action is a string representing an action to be called on
        # the parent FilterSet.
        parent_action = self.action or 'filter_{0}'.format(self.name)

        parent = getattr(self, 'parent', None)
        self.action = getattr(parent, parent_action, None)

        assert callable(self.action), (
            'Expected parent FilterSet `%s.%s` to have a `.%s()` method.' %
            (parent.__class__.__module__, parent.__class__.__name__, parent_action)
        )

    def filter(self, qs, value):
        """
        This filter method will act as a proxy for the actual method we want to
        call.
        It will try to find the method on the parent filterset,
        if not it attempts to search for the method `field_{{attribute_name}}`.
        Otherwise it defaults to just returning the queryset.
        """
        self.resolve_action()
        return self.action(self.name, qs, value)


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
