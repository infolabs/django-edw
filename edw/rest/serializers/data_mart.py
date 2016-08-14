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
    #view_class = serializers.CharField(read_only=True)

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
        fields = ('id', 'parent_id', 'name', 'slug', 'path', 'url', 'view_class', 'created_at', 'updated_at', 'level',
                  'active', 'description')


class DataMartListSerializer(DataMartSerializer):
    """
    DataMartListSerializer
    """
    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'url', 'active', 'view_class')


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
        return serializers.BooleanField().to_internal_value(value)

    def active_only_filter(self, data):
        if self.is_active_only:
            return data.active()
        else:
            return data

    @property
    @get_from_context_or_request('max_depth', None)
    def max_depth(self, value):
        '''
        :return: `max_depth` value in context or request, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @property
    def depth(self):
        '''
        :return: recursion depth
        '''
        raise NotImplementedError(
            '{cls}.depth must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def to_representation(self, data):
        max_depth = self.max_depth
        next_depth = self.depth + 1
        if max_depth is not None and next_depth > max_depth:
            data_marts = []
        else:
            data_marts = list(self.active_only_filter(data))
            for data_mart in data_marts:
                data_mart._depth = next_depth
        return super(_DataMartFilterMixin, self).to_representation(data_marts)


class DataMartTreeListField(_DataMartFilterMixin, serializers.ListField):
    """
    DataMartTreeListField
    """
    @property
    def depth(self):
        return self.parent._depth


class _DataMartTreeRootSerializer(_DataMartFilterMixin, serializers.ListSerializer):
    """
    Data Mart Tree Root Serializer
    """
    @property
    def depth(self):
        return 0


class DataMartTreeSerializer(DataMartSerializer):
    """
    Data Mart Tree Serializer
    """
    children = DataMartTreeListField(child=RecursiveField(), source='get_children', read_only=True)

    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'name', 'slug', 'url', 'active', 'view_class', 'children')
        list_serializer_class = _DataMartTreeRootSerializer

    def to_representation(self, data):
        """
        Prepare some data for children serialization
        """
        self._depth = data._depth
        return super(DataMartTreeSerializer, self).to_representation(data)
