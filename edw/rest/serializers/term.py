# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw.models.term import TermModel


class TermListField(serializers.ListField):
    '''
    Bla Bla...
    '''

    def to_representation(self, data):
        print "+++", self.parent._tmp

        print "* TermListField *", data
        #print dir(self)



        #print "+++", self.parent.instance



        #todo: PassTestResult

        #return []
        return super(TermListField, self).to_representation(data)



class TermSerializer(serializers.ModelSerializer):
    """
    A simple serializer to convert the terms data for rendering the select widget
    when looking up for a term.
    """
    name = serializers.CharField(read_only=True)
    children = TermListField(child=RecursiveField(), source='get_children', read_only=True)
    slug = serializers.SlugField(max_length=50, min_length=None, allow_blank=False)
    semantic_rule = serializers.ChoiceField(choices=TermModel.SEMANTIC_RULES)

    #text = serializers.SerializerMethodField()

    class Meta:
        model = TermModel
        fields = ('id', 'name', 'semantic_rule', 'children')


    def to_representation(self, data):

        #print "@ TermSerializer @", data

        self._tmp = data

        #todo: #1. self.context
        #todo: #2. ....
        #todo: PassTest
        #todo: treeInfo

        return super(TermSerializer, self).to_representation(data)


    '''
    def get_text(self, instance):
        return instance.slug
    '''