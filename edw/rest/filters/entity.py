# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import rest_framework_filters as filters

from rest_framework.exceptions import ValidationError
from rest_framework import serializers

from edw.models.entity import BaseEntity, EntityModel


class EntityFilter(filters.FilterSet):
    """
    EntityFilter
    """
    #active = filters.BooleanFilter()
    terms = filters.MethodFilter()

    class Meta:
        model = BaseEntity
        fields = ['active']

    def filter_terms(self, name, queryset, value):
        try:
            terms_ids = serializers.ListField(child=serializers.IntegerField()).to_internal_value(value.split(","))
        except ValidationError:
            return queryset

        print "*** filter_terms ***"
        print queryset.semantic_filter([1, 3])
        # print self, name, queryset, value, terms_ids

        print EntityModel.objects.indexable()

        return queryset