# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from edw.models.related.entity_file import BaseEntityFile


class EntityFileFilter(filters.FilterSet):
    """
    EntityImageFilter
    """
    entity = filters.NumberFilter()

    class Meta:
        model = BaseEntityFile
        fields = ['entity']
