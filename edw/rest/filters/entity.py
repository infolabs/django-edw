# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property
from django_filters.widgets import CSVWidget

import rest_framework_filters as filters

import django_filters

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from edw.models.entity import BaseEntity
from edw.models.data_mart import DataMartModel
from edw.rest.filters.decorators import get_from_underscore_or_data


class EntityFilter(filters.FilterSet):
    """
    EntityFilter
    """
    #active = filters.BooleanFilter()
    terms = filters.MethodFilter(widget=CSVWidget())
    data_mart_pk = filters.MethodFilter()

    class Meta:
        model = BaseEntity
        fields = ['active']

    @cached_property
    @get_from_underscore_or_data('terms', [], lambda value: value.split(","))
    def term_ids(self, value):
        '''
        :return: `term_ids` value parse from `self._term_ids` or `self.data['terms']`, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)

    @cached_property
    @get_from_underscore_or_data('use_cached_decompress', True)
    def use_cached_decompress(self, value):
        '''
        :return: `use_cached_decompress` value parse from `self._use_cached_decompress` or
            `self.data['use_cached_decompress']`, default: True
        '''
        return serializers.BooleanField().to_internal_value(value)

    @cached_property
    @get_from_underscore_or_data('data_mart_pk', None)
    def data_mart_id(self, value):
        '''
        :return: `data_mart_id` value parse from `self._data_mart_id` or
            `self.data['data_mart_pk']`, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @cached_property
    def data_mart(self):
        '''
        :return: active `DataMartModel` instance from `self.data_mart_id`
        '''
        #print "GET DATA MART", self.data_mart_id, self

        pk = self.data_mart_id
        if pk is not None:
            return get_object_or_404(DataMartModel.objects.active(), pk=pk)
        return None

    def filter_data_mart_pk(self, name, queryset, value):

        #print "*** filter_data_mart_pk ***", value, self, self._subset_cache

        #print "----------------------------"

        #print "***"

        self._data_mart_id = value
        if self.data_mart_id is None:
            return queryset

        #print "*** DM ID:", self.data_mart_id, self.data_mart

        #if self.data_mart:
        #    term_ids = list(self.data_mart.terms.active().values_list('id', flat=True))
        #else:
        #    term_ids = []

        #print "Active Terms::::", term_ids

        return queryset

    def filter_terms(self, name, queryset, value):
        self._term_ids = value
        if not self.term_ids:
            return queryset
        return queryset.semantic_filter(self.term_ids, use_cached_decompress=self.use_cached_decompress)
