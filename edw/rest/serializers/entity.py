# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import serializers

from edw.models.entity import EntityModel


class EntitySerializer(serializers.HyperlinkedModelSerializer):
    """
    A simple serializer to convert the entity items for rendering.
    """
    #active = serializers.BooleanField()

    class Meta:
        model = EntityModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}


class EntityDetailSerializer(EntitySerializer):
    """
    EntityDetailSerializer
    """
    class Meta(EntitySerializer.Meta):
        fields = ('id', 'url', 'created_at', 'updated_at', 'active')


class EntityListSerializer(EntitySerializer):
    """
    EntityListSerializer
    """
    class Meta(EntitySerializer.Meta):
        fields = ('id', 'url', 'active')

