# -*- coding: utf-8 -*-
from __future__ import unicode_literals

#from django.utils.functional import cached_property

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

        #print "* TermListField *", data
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
        print "* is_active_only:", self.is_active_only


        #print "@ TermSerializer @", self.instance, self.root.instance

        self._tmp = data

        #todo: #1. self.context
        #todo: #2. ....
        #todo: PassTest
        #todo: treeInfo

        return super(TermSerializer, self).to_representation(data)

    @property
    def is_active_only(self):
        '''
        :return:
        active_only value in context or request, default: True
        '''
        result = self.context.get('active_only')
        if result is None:
            result = True
            request = self.context.get('request')
            if request:
                value = request.GET.get('active_only')
                if not value is None:
                    result = serializers.BooleanField().to_representation(value)
            self.context['active_only'] = result
        return result

    #todo: selected property