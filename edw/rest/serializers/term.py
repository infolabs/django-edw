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


class _TermsFilterMixin(object):
    '''
    If `active_only` parameter set `True`, then add filtering by `active` = `True`
    '''
    @property
    @get_from_context_or_request('active_only', True)
    def is_active_only(self, value):
        '''
        :return:
        `active_only` value in context or request, default: True
        '''
        return serializers.BooleanField().to_representation(value)

    def active_only_filter(self, data):
        if self.is_active_only:
            return data.active()
        else:
            return data

    def get_selected_terms(self):
        '''
        :return:
        `None` if parent node not selected, or selected child dict.
        '''
        raise NotImplementedError(
            '{cls}.get_selected_terms() must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @property
    def is_expanded_specification(self):
        '''
        :return:
        `True` if parent node specification mode is `expanded`.
        '''
        raise NotImplementedError(
            '{cls}.is_expanded_specification must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def to_representation(self, data):
        terms = list(self.active_only_filter(data))

        print "===================================================="

        selected_terms = self.get_selected_terms()

        print ">>> is_expanded_specification", self.is_expanded_specification

        if self.is_expanded_specification or not selected_terms is None:
            for term in terms:
                try:
                    term._selected_term_info = selected_terms.pop(term.id)
                except (KeyError, AttributeError):
                    term._selected_term_info = None
        else:
            terms = []

        print "===================================================="

        return super(_TermsFilterMixin, self).to_representation(terms)


class TermTreeListField(_TermsFilterMixin, serializers.ListField):
    '''
    TermTreeListField
    '''
    def get_selected_terms(self):
        term_info = self.parent._selected_term_info
        return None if term_info is None else term_info.get_children_dict()

    @property
    def is_expanded_specification(self):
        return self.parent._is_expanded_specification

    def to_representation(self, data):
        print "* TermListField *", data
        #todo: PassTestResult
        #return []
        return super(TermTreeListField, self).to_representation(data)


class _TermTreeRootSerializer(_TermsFilterMixin, serializers.ListSerializer):
    """
    Term Tree Root Serializer
    """

    def get_selected_terms(self):
        tree = TermModel.decompress(self.selected, self.fix_it)
        return tree.root.get_children_dict()

    @property
    def is_expanded_specification(self):
        return True

    '''
    def to_representation(self, data):
        return super(_TermTreeRootSerializer, self).to_representation(data)
    '''

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


class TermTreeSerializer(TermSerializer):
    """
    Term Tree Serializer
    """
    children = TermTreeListField(child=RecursiveField(), source='get_children', read_only=True)
    is_selected = serializers.SerializerMethodField()

    class Meta(TermSerializer.Meta):
        fields = ('id', 'name', 'slug', 'path', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'is_selected', 'children')
        list_serializer_class = _TermTreeRootSerializer

    def to_representation(self, data):
        """
        Prepare some data for children serialization
        """
        self._selected_term_info = data._selected_term_info
        self._is_expanded_specification = data.specification_mode == TermModel.EXPANDED_SPECIFICATION

        print "@ TermSerializer: to_representation @", data

        return super(TermSerializer, self).to_representation(data)

    def get_is_selected(self, instance):
        return not self._selected_term_info is None