# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from edw.models.data_mart import BaseDataMart


class DataMartFilter(filters.FilterSet):
    """
    DataMartFilter
    """
    active = filters.BooleanFilter(name="active")
    parent_id = filters.NumberFilter(name='parent_id')

    class Meta:
        model = BaseDataMart
        fields = ['active', ]

    def filter_parent_id(self, name, queryset, value):
        if value:
            return queryset.filter(parent_id=value)
        return queryset