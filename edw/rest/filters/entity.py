# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property
from django_filters.widgets import CSVWidget

import rest_framework_filters as filters

from rest_framework import serializers

from edw.models.entity import BaseEntity
from edw.rest.filters.decorators import get_from_underscore_or_data


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
    @get_from_underscore_or_data([], lambda value: value.split(","))
    def term_ids(self, value):
        '''
        :return: `term_ids` value parse from `self._term_ids` or `self.data['term_ids']`, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)

    @cached_property
    @get_from_underscore_or_data(True)
    def use_cached_decompress(self, value):
        '''
        :return: `use_cached_decompress` value parse from `self._use_cached_decompress` or
            `self.data['use_cached_decompress']`, default: True
        '''
        return serializers.BooleanField().to_internal_value(value)

    def filter_terms(self, name, queryset, value):
        self._term_ids = value
        if not self.term_ids:
            return queryset
        return queryset.semantic_filter(self.term_ids, use_cached_decompress=self.use_cached_decompress)
