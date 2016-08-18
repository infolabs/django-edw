# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from edw.models.entity import BaseEntity


class EntityFilter(filters.FilterSet):
    """
    EntityFilter
    """
    active = filters.BooleanFilter(name="active")

    class Meta:
        model = BaseEntity
        fields = ['active']
