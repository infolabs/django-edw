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
        '''
        Semantic filter, use cached decompress by default
        :param name:
        :param queryset:
        :param value:
        :return:
        '''
        try:
            terms_ids = serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)
        except ValidationError:
            return queryset
        try:
            use_cached_decompress = serializers.BooleanField().to_internal_value(self.data.get('use_cached_decompress'))
        except ValidationError:
            use_cached_decompress = True
        return queryset.semantic_filter(terms_ids, use_cached_decompress=use_cached_decompress)
