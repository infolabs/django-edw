# -*- coding: utf-8 -*-
"""
E1 test stub: minimal stand-in for djangorestframework-filters.

Only the declarations used by django-edw filter sets are needed to import the
REST serializer layer offline. Filtering itself is not part of the E1 contract.
"""
from __future__ import unicode_literals


class FilterSet(object):
    """Lightweight filter set: collects declared filters, keeps a queryset."""

    base_filters = {}

    def __init__(self, data=None, queryset=None, **kwargs):
        self.data = data if data is not None else {}
        self.queryset = queryset
        self.qs = queryset

    @property
    def filters(self):
        return dict(self.base_filters)

    def filter_queryset(self, queryset):
        return queryset


class Filter(object):
    """Common filter descriptor accepting django-filter style arguments."""

    def __init__(self, name=None, lookup_expr=None, label=None, widget=None,
                 action=None, **kwargs):
        self.name = name
        self.lookup_expr = lookup_expr
        self.label = label
        self.widget = widget
        self.action = action or ''
        self.extra = kwargs

    @property
    def field_name(self):
        return self.name

    @field_name.setter
    def field_name(self, value):
        self.name = value


class CharFilter(Filter):
    pass


class BooleanFilter(Filter):
    pass


class NumberFilter(Filter):
    pass


class ChoiceFilter(Filter):
    def __init__(self, *args, **kwargs):
        self.choices = kwargs.pop('choices', ())
        super(ChoiceFilter, self).__init__(*args, **kwargs)


class IsoDateTimeFilter(Filter):
    pass


class DateRangeFilter(Filter):
    pass


class MethodFilter(Filter):
    pass


__all__ = [
    'FilterSet', 'Filter', 'CharFilter', 'BooleanFilter', 'NumberFilter',
    'ChoiceFilter', 'IsoDateTimeFilter', 'DateRangeFilter', 'MethodFilter',
]
