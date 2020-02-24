# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import six

from django.utils.translation import ugettext_lazy as _

import rest_framework_filters as filters
try:
    from rest_framework_filters import MethodFilter
except ImportError:
    from .common import MethodFilter

from rest_framework import serializers

from edw.models.data_mart import BaseDataMart

from .common import NumberInFilter


class DataMartFilter(filters.FilterSet):
    """
    DataMartFilter
    """
    #active = filters.BooleanFilter()
    parent_id = MethodFilter(label=_("Parent Id"))
    id__in = NumberInFilter(name='id', label=_("IDs"))
    slug = filters.CharFilter(lookup_expr='iexact', label=_("Slug"))
    slug__icontains = filters.CharFilter(name='slug', lookup_expr='icontains', label=_("Slug (icontains)"))
    path = filters.CharFilter(lookup_expr='iexact', label=_("Path"))
    path__icontains = filters.CharFilter(name='path', lookup_expr='icontains', label=_("Path (icontains)"))

    class Meta:
        model = BaseDataMart
        fields = ['active']

    def filter_parent_id(self, name, queryset, value):
        key = name
        try:
            value = int(value)
        except ValueError:
            if value.lower() in ('none', 'null'):
                value = None
            else:
                key = 'parent__slug'
        return queryset.filter(**{"{}__exact".format(key): value})
