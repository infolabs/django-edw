# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.cache import cache
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
    @cached_property
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

    @cached_property
    def is_expanded_specification(self):
        '''
        :return: `True` if parent node specification mode is `expanded`
        '''
        raise NotImplementedError(
            '{cls}.is_expanded_specification must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @cached_property
    @get_from_context_or_request('max_depth', None)
    def max_depth(self, value):
        '''
        :return: `max_depth` value in context or request, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @cached_property
    def depth(self):
        '''
        :return: recursion depth
        '''
        raise NotImplementedError(
            '{cls}.depth must be implemented.'.format(
                cls=self.__class__.__name__
            )
        )

    @cached_property
    @get_from_context_or_request('cached', True)
    def cached(self, value):
        '''
        :return: `cached` value in context or request, default: True
        '''
        return serializers.BooleanField().to_internal_value(value)

    @staticmethod
    def on_cache_set(key):
        buf = TermModel.get_children_buffer()
        old_key = buf.record(key)
        if old_key != buf.empty:
            cache.delete(old_key)

    def prepare_data(self, data):
        if self.cached:
            return data.cache(on_cache_set=_TermsFilterMixin.on_cache_set, timeout=TermModel.CHILDREN_CACHE_TIMEOUT)
        else:
            return data.prepare_for_cache(data)

    def to_representation(self, data):
        next_depth = self.depth + 1
        if self.max_depth is not None and next_depth > self.max_depth:
            terms = []
        else:
            selected_terms = self.get_selected_terms()
            if self.is_expanded_specification or selected_terms is not None:
                terms = self.prepare_data(self.active_only_filter(data))
                for term in terms:
                    term._depth = next_depth
                    try:
                        term._selected_term_info = selected_terms.pop(term.id)
                    except (KeyError, AttributeError):
                        term._selected_term_info = None
            else:
                terms = []
        return super(_TermsFilterMixin, self).to_representation(terms)


class TermTreeListField(_TermsFilterMixin, serializers.ListField):
    """
    TermTreeListField
    """
    def get_selected_terms(self):
        term_info = self.parent._selected_term_info
        return None if term_info is None else term_info.get_children_dict()

    @cached_property
    def is_expanded_specification(self):
        return self.parent._is_expanded_specification

    @cached_property
    def depth(self):
        return self.parent._depth


class _TermTreeRootSerializer(_TermsFilterMixin, serializers.ListSerializer):
    """
    Term Tree Root Serializer
    """
    def get_selected_terms(self):
        selected = self.selected[:]
        has_selected = bool(selected)

        if self.data_mart:
            trunk = list(self.active_only_filter(self.data_mart.terms.values_list('id', flat=True)))
        else:
            trunk = []

        if trunk:
            selected.extend(trunk)
        else:
            trunk = list(self.active_only_filter(self.instance).values_list('id', flat=True))

        decompress = TermModel.cached_decompress if self.cached else TermModel.decompress

        trunk = decompress(trunk, self.fix_it)
        if has_selected:
            tree = decompress(selected, self.fix_it)
        else:
            tree = trunk

        for k, v in trunk.items():
            x = tree.get(k)
            if x is not None:
                if v.is_leaf:
                    x.attrs['structure'] = 'limb'
                else:
                    x.attrs['structure'] = 'trunk'

        return tree.root.get_children_dict()

    @cached_property
    def is_expanded_specification(self):
        return True

    @cached_property
    @get_from_context_or_request('fix_it', False)
    def fix_it(self, value):
        '''
        :return: `fix_it` value in context or request, default: False
        '''
        return serializers.BooleanField().to_internal_value(value)

    @cached_property
    @get_from_context_or_request('selected', [])
    def selected(self, value):
        '''
        :return: `selected` terms ids in context or request, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value.split(","))

    @cached_property
    @get_from_context('data_mart')
    def data_mart(self):
        '''
        :return: active `DataMartModel` instance from context, if `data_mart` not set, try find object by parsing request
        '''
        def get_queryset():
            return DataMartModel.objects.active()

        pk = self.data_mart_pk
        if pk is not None:
            return get_object_or_404(get_queryset(), pk=pk)
        else:
            path = self.data_mart_path
            if path is not None:
                return get_object_or_404(get_queryset(), path=path)
        return None

    @cached_property
    @get_from_context_or_request('data_mart_pk', None)
    def data_mart_pk(self, value):
        '''
        :return: `data_mart_pk` data mart id in context or request, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @cached_property
    @get_from_context_or_request('data_mart_path', None)
    def data_mart_path(self, value):
        '''
        :return: `data_mart_path` data mart path in context or request, default: None
        '''
        return serializers.CharField().to_internal_value(value)

    @cached_property
    def depth(self):
        return 0


class TermTreeSerializer(TermSerializer):
    """
    Term Tree Serializer
    """
    children = TermTreeListField(child=RecursiveField(), source='get_children', read_only=True)
    structure = serializers.SerializerMethodField()

    class Meta(TermSerializer.Meta):
        fields = ('id', 'name', 'slug', 'semantic_rule', 'specification_mode', 'url', 'active',
                  'attributes', 'view_class', 'structure', 'children')
        list_serializer_class = _TermTreeRootSerializer

    def to_representation(self, data):
        """
        Prepare some data for children serialization
        """
        self._depth = data._depth
        self._selected_term_info = data._selected_term_info
        self._is_expanded_specification = data.specification_mode == TermModel.EXPANDED_SPECIFICATION
        return super(TermSerializer, self).to_representation(data)

    def get_structure(self, instance):
        if self._selected_term_info is not None:
            return self._selected_term_info.attrs.get('structure', 'branch')
        return None  # 'twig', node not selected
