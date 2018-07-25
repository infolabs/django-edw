# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from edw.models.related.entity_image import BaseEntityImage


class EntityImageFilter(filters.FilterSet):
    """
    EntityImageFilter
    """
    entity = filters.NumberFilter()

    class Meta:
        model = BaseEntityImage
        fields = ['entity']
