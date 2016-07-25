# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw.models.term import TermModel


class TermSelectSerializer(serializers.ModelSerializer):
    """
    A simple serializer to convert the terms data for rendering the select widget
    when looking up for a term.
    """
    #parent = RecursiveField(allow_null=True)
    name = serializers.CharField(read_only=True)
    children = serializers.ListField(child=RecursiveField(), source='get_children', read_only=True)


    #text = serializers.SerializerMethodField()

    class Meta:
        model = TermModel
        fields = ('id', 'name', 'children')

    '''
    def get_text(self, instance):
        return instance.entity_name
    '''