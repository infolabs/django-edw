# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.functional import cached_property

from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework_recursive.fields import RecursiveField

from edw.models.term import TermModel
from edw.models.data_mart import DataMartModel
from edw.rest.serializers.decorators import get_from_context_or_request, get_from_context


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
        fields = ('id', 'parent_id', 'name', 'slug', 'path', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'description', 'view_class', 'created_at', 'updated_at', 'level', 'attributes')


class TermListSerializer(TermSerializer):
    '''
    TermListSerializer
    '''
    class Meta(TermSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'view_class', 'attributes')


class _TermsFilterMixin(object):
    '''
    If `active_only` parameter set `True`, then add filtering by `active` = `True`
    '''
    @property
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

    def get_selected_terms(self):
        '''
        :return: `None` if parent node not selected, or selected child dict
        '''
        raise NotImplementedError(
            '{cls}.get_selected_terms() must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @property
    def is_expanded_specification(self):
        '''
        :return: `True` if parent node specification mode is `expanded`
        '''
        raise NotImplementedError(
            '{cls}.is_expanded_specification must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    def to_representation(self, data):
        terms = list(self.active_only_filter(data))
        selected_terms = self.get_selected_terms()
        if self.is_expanded_specification or not selected_terms is None:
            for term in terms:
                try:
                    term._selected_term_info = selected_terms.pop(term.id)
                except (KeyError, AttributeError):
                    term._selected_term_info = None
        else:
            terms = []
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

    '''
    def to_representation(self, data):
        return super(TermTreeListField, self).to_representation(data)
    '''

class _TermTreeRootSerializer(_TermsFilterMixin, serializers.ListSerializer):
    """
    Term Tree Root Serializer
    """

    def get_selected_terms(self):

        print "*************************************************"

        selected = self.selected[:]
        fix_it = self.fix_it

        has_selected = bool(selected)

        data_mart = self.data_mart

        print data_mart

        if data_mart:
            terms_ids_qs = data_mart.terms.values_list('id', flat=True)
            if self.is_active_only:
                trunk = list(terms_ids_qs.active())
            else:
                trunk = list(terms_ids_qs)
        else:
            trunk = []

        if trunk:
            selected.extend(trunk)
        else:
            trunk = list(self.active_only_filter(self.instance).values_list('id', flat=True))

        trunk = TermModel.decompress(trunk, fix_it) # need cache
        if has_selected:
            tree = TermModel.decompress(selected, fix_it) # need cache
        else:
            tree = trunk

        '''
        tree.root.attrs['trunk'] = True
        for k, v in trunk.items():
            x = tree.get(k)
            if not x is None:
                if v.is_leaf:
                    x.attrs['branch'] = True
                else:
                    x.attrs['trunk'] = True
        '''

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
        :return: `fix_it` value in context or request, default: False
        '''
        return serializers.BooleanField().to_internal_value(value)

    @property
    @get_from_context_or_request('selected', [])
    def selected(self, value):
        '''
        :return: `selected` terms ids in context or request, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value.split(","))

    @property
    @get_from_context('data_mart')
    def data_mart(self):
        '''
        :return: active `DataMartModel` instance from context, if `data_mart` not set, try find object by parsing request
        '''
        def get_queryset():
            return DataMartModel.objects.active()

        pk = self.data_mart_id
        if not pk is None:
            return get_object_or_404(get_queryset(), pk=pk)
        else:
            path = self.data_mart_path
            if not path is None:
                return get_object_or_404(get_queryset(), path=path)
        return None

    @property
    @get_from_context_or_request('data_mart_id', None)
    def data_mart_id(self, value):
        '''
        :return: `data_mart_id` data mart id in context or request, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @property
    @get_from_context_or_request('data_mart_path', None)
    def data_mart_path(self, value):
        '''
        :return: `data_mart_path` data mart path in context or request, default: None
        '''
        return serializers.CharField().to_internal_value(value)


class TermTreeSerializer(TermSerializer):
    """
    Term Tree Serializer
    """
    children = TermTreeListField(child=RecursiveField(), source='get_children', read_only=True)
    is_selected = serializers.SerializerMethodField()

    class Meta(TermSerializer.Meta):
        fields = ('id', 'name', 'slug', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'is_selected', 'attributes', 'view_class', 'children')
        list_serializer_class = _TermTreeRootSerializer

    def to_representation(self, data):
        """
        Prepare some data for children serialization
        """
        self._selected_term_info = data._selected_term_info
        self._is_expanded_specification = data.specification_mode == TermModel.EXPANDED_SPECIFICATION
        return super(TermSerializer, self).to_representation(data)

    def get_is_selected(self, instance):
        return not self._selected_term_info is None