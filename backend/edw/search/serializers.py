# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer

from edw.search.indexes import EntityIndex


class EntitySearchSerializer(HaystackSerializer):
    """
    The base serializer to represent one or more entity fields for being returned as a
    result list during searches.
    """
    entity_url = serializers.SerializerMethodField()

    class Meta:
        index_classes = [EntityIndex]

        fields = ('entity_name', 'entity_model', 'entity_url', 'text', 'autocomplete')
        ignore_fields = ('text', 'autocomplete')

        field_aliases = {'q': 'text'}



    def get_entity_url(self, search_result):

        if search_result.object:
            return search_result.object.get_absolute_url(
                request=self.context.get('request'), format=self.context.get('format'))
