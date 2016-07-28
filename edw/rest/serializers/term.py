# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw.models.term import TermModel


#class TermSerializer(serializers.ModelSerializer):
class TermSerializer(serializers.HyperlinkedModelSerializer):
    """
    A simple serializer to convert the terms data for rendering the select widget
    when looking up for a term.
    """
    #name = serializers.CharField(read_only=True)
    #slug = serializers.SlugField(max_length=50, min_length=None, allow_blank=False)
    #path = serializers.CharField(max_length=255, allow_blank=False, read_only=True)
    #semantic_rule = serializers.ChoiceField(choices=TermModel.SEMANTIC_RULES)
    #specification_mode = serializers.ChoiceField(choices=TermModel.SPECIFICATION_MODES)
    #active = serializers.BooleanField()

    #text = serializers.SerializerMethodField()

    class Meta:
        model = TermModel
        fields = ('id', 'name', 'slug', 'path', 'semantic_rule', 'specification_mode', 'url', 'active')
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}


    '''
    def get_text(self, instance):
        return instance.slug
    '''


class TermTreeListField(serializers.ListField):
    '''
    TermTreeListField
    '''

    def to_representation(self, data):
        print "+++", self.parent._tmp

        print "* TermListField *", data
        #print dir(self)


        #print "+++", self.parent.instance


        #todo: PassTestResult

        #return []
        return super(TermTreeListField, self).to_representation(data)


class TermTreeSerializer(TermSerializer):
    """
    Term Tree Serializer
    """
    children = TermTreeListField(child=RecursiveField(), source='get_children', read_only=True)

    class Meta(TermSerializer.Meta):
        fields = ('id', 'name', 'slug', 'path', 'semantic_rule', 'specification_mode', 'url', 'children')

    def to_representation(self, data):

        print "@ TermSerializer @", dir(TermModel)

        self._tmp = data

        #todo: #1. self.context
        #todo: #2. ....
        #todo: PassTest
        #todo: treeInfo

        return super(TermSerializer, self).to_representation(data)

