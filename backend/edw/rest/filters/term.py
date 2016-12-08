# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.generics import get_object_or_404

import rest_framework_filters as filters

from edw.models.term import BaseTerm, TermModel
from edw.models.data_mart import DataMartModel
from edw.rest.filters.decorators import get_from_underscore_or_data


class TermFilter(filters.FilterSet):
    """
    TermFilter
    """
    #active = filters.BooleanFilter()
    parent_id = filters.NumberFilter()
    semantic_rule = filters.ChoiceFilter(name="semantic_rule", choices=BaseTerm.SEMANTIC_RULES + (('', _('Any')), ))
    specification_mode = filters.ChoiceFilter(name="specification_mode",
                                              choices=BaseTerm.SPECIFICATION_MODES + (('', _('Any')), ))
    data_mart_pk = filters.MethodFilter()

    class Meta:
        model = BaseTerm
        fields = ['active']

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
        pk = self.data_mart_id
        if pk is not None:
            return get_object_or_404(DataMartModel.objects.active(), pk=pk)
        return None

    @cached_property
    def data_mart_term_ids(self):
        return self.data_mart.active_terms_ids if self.data_mart else []

    def filter_data_mart_pk(self, name, queryset, value):
        self._data_mart_id = value
        if self.data_mart_id is None:
            return queryset
        return queryset.filter(id__in=TermModel.decompress(self.data_mart_term_ids, fix_it=True).keys())



