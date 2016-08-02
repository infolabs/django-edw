# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django.utils.translation import ugettext_lazy as _

import rest_framework_filters as filters

from edw.models.data_mart import BaseDataMart


class DataMartFilter(filters.FilterSet):
    """
    DataMartFilter
    """
    active = filters.BooleanFilter(name="active")

    class Meta:
        model = BaseDataMart
        fields = ['active', ]

