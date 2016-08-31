# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import serializers

from edw.models.entity import EntityModel


class AttributeSerializer(serializers.Serializer):
    """
    A serializer to convert the characteristics and marks for rendering.
    """
    name = serializers.CharField()
    path = serializers.CharField()
    values = serializers.ListField(child=serializers.CharField())
    view_class = serializers.ListField(child=serializers.CharField())


class EntitySerializer(serializers.HyperlinkedModelSerializer):
    """
    A simple serializer to convert the entity items for rendering.
    """
    #active = serializers.BooleanField()
    characteristics = AttributeSerializer(read_only=True, many=True)
    marks = AttributeSerializer(read_only=True, many=True)

    class Meta:
        model = EntityModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}


class EntityDetailSerializer(EntitySerializer):
    """
    EntityDetailSerializer
    """
    class Meta(EntitySerializer.Meta):
        fields = ('id', 'url', 'created_at', 'updated_at', 'active', 'characteristics', 'marks')


class EntityListSerializer(EntitySerializer):
    """
    EntityListSerializer
    """
    short_characteristics = AttributeSerializer(read_only=True, many=True)
    short_marks = AttributeSerializer(read_only=True, many=True)

    class Meta(EntitySerializer.Meta):
        fields = ('id', 'url', 'active', 'short_characteristics', 'short_marks')

