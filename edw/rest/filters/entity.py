# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django_filters.widgets import CSVWidget

import rest_framework_filters as filters

from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from edw.models.entity import BaseEntity


class EntityFilter(filters.FilterSet):
    """
    EntityFilter
    """
    #active = filters.BooleanFilter()
    terms = filters.MethodFilter(widget=CSVWidget())

    class Meta:
        model = BaseEntity
        fields = ['active']

    def filter_terms(self, name, queryset, value):
        try:
            terms_ids = serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)
        except ValidationError:
            return queryset
        return queryset.semantic_filter(terms_ids)
