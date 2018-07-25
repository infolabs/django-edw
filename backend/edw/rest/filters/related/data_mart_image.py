# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from edw.models.related.data_mart_image import BaseDataMartImage


class DataMartImageFilter(filters.FilterSet):
    """
    DataMartImageFilter
    """
    data_mart = filters.NumberFilter()

    class Meta:
        model = BaseDataMartImage
        fields = ['data_mart']
