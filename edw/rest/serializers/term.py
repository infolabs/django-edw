# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django.utils.functional import cached_property

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw.models.term import TermModel
from edw.rest.serializers.decorators import get_from_context_or_request


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
    #description = serializers.CharField(read_only=True)

    parent_id = serializers.SerializerMethodField()

    class Meta:
        model = TermModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}

    def get_parent_id(self, instance):
        return instance.parent_id


class TermDetailSerializer(TermSerializer):
    '''
    TermDetailSerializer
    '''
    class Meta(TermSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'path', 'semantic_rule', 'specification_mode', 'url', 'active', 'description')


class TermListSerializer(TermSerializer):
    '''
    TermListSerializer
    '''
    class Meta(TermSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'path', 'semantic_rule', 'specification_mode', 'url', 'active')



class TermTreeListField(serializers.ListField):
    '''
    TermTreeListField
    '''
    def to_representation(self, data):
        #print "+++", self.parent._tmp

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

        print "-----------------"
        #print "* is_active_only:", self.is_active_only

        print "+++++++++++++++++"
        print "-<*>->", self.is_active_only

        print "* selected:", self.selected

        print "@ TermSerializer @", self.__class__, self.root.__class__


        #todo: #1. self.context
        #todo: #2. ....
        #todo: PassTest
        #todo: treeInfo
        return super(TermSerializer, self).to_representation(data)

    @property
    @get_from_context_or_request('active_only', True)
    def is_active_only(self, value):
        '''
        :return:
        `active_only` value in context or request, default: True
        '''
        return serializers.BooleanField().to_representation(value)

    @property
    @get_from_context_or_request('fix_it', False)
    def fix_it(self, value):
        '''
        :return:
        `fix_it` value in context or request, default: False
        '''
        return serializers.BooleanField().to_representation(value)

    @property
    @get_from_context_or_request('selected', [])
    def selected(self, value):
        '''
        :return:
        `selected` terms ids in context or request, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value.split(","))

    @property
    def tree(self):
        '''

        :return:
        '''
        return None