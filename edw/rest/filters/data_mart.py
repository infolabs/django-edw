# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from edw.models.data_mart import BaseDataMart


class DataMartFilter(filters.FilterSet):
    """
    DataMartFilter
    """
    #active = filters.BooleanFilter()
    parent_id = filters.NumberFilter()

    class Meta:
        model = BaseDataMart
        fields = ['active']
