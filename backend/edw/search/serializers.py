# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer

from edw.search.indexes import EntityIndex


class EntitySearchSerializer(HaystackSerializer):
    """
    The base serializer to represent one or more entity fields for being returned as a
    result list during searches.
    """
    #price = serializers.SerializerMethodField()

    class Meta:
        index_classes = [EntityIndex]

        fields = ('text', 'autocomplete', 'entity_name', 'entity_model', 'entity_url',)
        '''
        ignore_fields = ('text', 'autocomplete',)
        field_aliases = {'q': 'text'}
        '''

    '''
    def get_price(self, search_result):
        """
        The price can't be stored inside the search index but must be fetched from the resolved
        model. In case your product models have a fixed price, try to store it as
        ``indexes.DecimalField`` and retrieve from the search index, because that's much faster.
        """
        if search_result.object:
            return search_result.object.get_price(self.context['request'])
    '''