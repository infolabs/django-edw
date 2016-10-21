# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.cache import cache
from django.utils.functional import cached_property

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw.models.data_mart import DataMartModel
from edw.rest.serializers.decorators import get_from_context_or_request


class DataMartSerializer(serializers.HyperlinkedModelSerializer):
    """
    A simple serializer to convert the data mart items for rendering.
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
    rel = serializers.SerializerMethodField()

    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'path', 'url', 'view_class', 'created_at', 'updated_at', 'level',
                  'active', 'rel', 'description')

    def get_rel(self, instance):
        return ['{}{}'.format(relation.term_id, relation.direction) for relation in instance.relations.all()]


class DataMartSummarySerializer(DataMartSerializer):
    """
    DataMartSummarySerializer
    """
    class Meta(DataMartSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'url', 'active', 'view_class')


class _DataMartFilterMixin(object):
    """
    If `active_only` parameter set `True`, then add filtering by `active` = `True`
    """
    @cached_property
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

    @cached_property
    @get_from_context_or_request('max_depth', None)
    def max_depth(self, value):
        '''
        :return: `max_depth` value in context or request, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @cached_property
    def depth(self):
        '''
        :return: recursion depth
        '''
        raise NotImplementedError(
            '{cls}.depth must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @cached_property
    @get_from_context_or_request('cached', True)
    def cached(self, value):
        '''
        :return: `cached` value in context or request, default: True
        '''
        return serializers.BooleanField().to_internal_value(value)

    @staticmethod
    def on_cache_set(key):
        buf = DataMartModel.get_children_buffer()
        old_key = buf.record(key)
        if old_key != buf.empty:
            cache.delete(old_key)

    def prepare_data(self, data):
        if self.cached:
            return data.cache(on_cache_set=_DataMartFilterMixin.on_cache_set,
                              timeout=DataMartModel.CHILDREN_CACHE_TIMEOUT)
        else:
            return data.prepare_for_cache(data)

    def to_representation(self, data):
        max_depth = self.max_depth
        next_depth = self.depth + 1
        if max_depth is not None and next_depth > max_depth:
            data_marts = []
        else:
            data_marts = self.prepare_data(self.active_only_filter(data))
            for data_mart in data_marts:
                data_mart._depth = next_depth
        return super(_DataMartFilterMixin, self).to_representation(data_marts)


class DataMartTreeListField(_DataMartFilterMixin, serializers.ListField):
    """
    DataMartTreeListField
    """
    @cached_property
    def depth(self):
        return self.parent._depth


class _DataMartTreeRootSerializer(_DataMartFilterMixin, serializers.ListSerializer):
    """
    Data Mart Tree Root Serializer
    """
    @cached_property
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
