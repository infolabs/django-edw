# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property
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

    @cached_property
    def use_cached_decompress(self):
        '''
        :return: `use_cached_decompress` value from `self.data`, default: True
        '''
        try:
            return serializers.BooleanField().to_internal_value(self.data.get('use_cached_decompress'))
        except ValidationError:
            return True

    def filter_terms(self, name, queryset, value):
        try:
            terms_ids = serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)
        except ValidationError:
            return queryset
        return queryset.semantic_filter(terms_ids, use_cached_decompress=self.use_cached_decompress)
