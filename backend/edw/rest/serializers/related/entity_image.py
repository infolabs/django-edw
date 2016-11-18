# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import serializers

from edw.models.related import EntityImageModel


class EntityImageSerializer(serializers.ModelSerializer):
    """
    Common serializer for the EntityImage model.
    """

    class Meta:
        model = EntityImageModel
        #extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}
        fields = '__all__'