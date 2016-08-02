# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw.models.data_mart import DataMartModel
from edw.rest.serializers.decorators import get_from_context_or_request


class DataMartSerializer(serializers.HyperlinkedModelSerializer):
    """
    A simple serializer to convert the data mart items for rendering
    when looking up for a term.
    """
    #name = serializers.CharField(read_only=True)
    #slug = serializers.SlugField(max_length=50, min_length=None, allow_blank=False)
    #path = serializers.CharField(max_length=255, allow_blank=False, read_only=True)
    #active = serializers.BooleanField()
    #description = serializers.CharField(read_only=True)

    parent_id = serializers.SerializerMethodField()

    class Meta:
        model = DataMartModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}

    def get_parent_id(self, instance):
        return instance.parent_id


class DataMartDetailSerializer(DataMartSerializer):
    """
    DataMartDetailSerializer
    """
    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'path', 'url', 'active', 'description')


class DataMartListSerializer(DataMartSerializer):
    """
    DataMartListSerializer
    """
    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'url', 'active')


class _DataMartFilterMixin(object):
    """
    If `active_only` parameter set `True`, then add filtering by `active` = `True`
    """
    @property
    @get_from_context_or_request('active_only', True)
    def is_active_only(self, value):
        '''
        :return: `active_only` value in context or request, default: True
        '''
        return serializers.BooleanField().to_representation(value)

    def active_only_filter(self, data):
        if self.is_active_only:
            return data.active()
        else:
            return data

    def to_representation(self, data):
        return super(_DataMartFilterMixin, self).to_representation(self.active_only_filter(data))


class DataMartTreeListField(_DataMartFilterMixin, serializers.ListField):
    """
    DataMartTreeListField
    """


class _DataMartTreeRootSerializer(_DataMartFilterMixin, serializers.ListSerializer):
    """
    Data Mart Tree Root Serializer
    """


class DataMartTreeSerializer(DataMartSerializer):
    """
    Data Mart Tree Serializer
    """
    children = DataMartTreeListField(child=RecursiveField(), source='get_children', read_only=True)

    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'name', 'slug', 'url', 'active', 'children')
        list_serializer_class = _DataMartTreeRootSerializer

