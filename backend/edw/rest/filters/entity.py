# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import urllib

from django.utils import six
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from django.template import loader
from django.db.models.expressions import BaseExpression
from django.http import Http404

import rest_framework_filters as filters

from rest_framework.compat import template_render
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from rest_framework.filters import OrderingFilter, BaseFilterBackend

from edw.models.entity import BaseEntity
from edw.models.term import TermModel
from edw.models.data_mart import DataMartModel
from edw.models.rest import DynamicFilterSetMixin, DynamicFilterMixin
from edw.rest.filters.decorators import get_from_underscore_or_data
from edw.rest.filters.widgets import CSVWidget

from .common import NumberInFilter


class BaseEntityFilter(filters.FilterSet):
    """
    BaseEntityFilter
    """
    terms = filters.MethodFilter(widget=CSVWidget(), label=_("Terms"))
    data_mart_pk = filters.MethodFilter(label=_("Data mart"))

    def __init__(self, data, **kwargs):
        try:
            data['_mutable'] = True
        except AttributeError:
            data = data.copy()
        self.patch_data(data, **kwargs)
        super(BaseEntityFilter, self).__init__(data, **kwargs)

    def patch_data(self, data, **kwargs):
        self._data_mart = data.get('_data_mart', None)
        tree = TermModel.cached_decompress([], fix_it=True)
        data.update({
            '_initial_filter_meta': tree,
            '_terms_filter_meta': tree,
            '_data_mart': None,
            '_terms_ids': []
        })

    @cached_property
    @get_from_underscore_or_data('terms', [], lambda value: urllib.unquote(value).decode('utf8').split(","))
    def term_ids(self, value):
        '''
        :return: `term_ids` value parse from `self._term_ids` or `self.data['terms']`, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)

    def filter_terms(self, name, queryset, value):
        msg = "Method filter_terms() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @cached_property
    @get_from_underscore_or_data('data_mart_pk', None)
    def data_mart_id(self, value):
        '''
        :return: `data_mart_id` value parse from `self._data_mart_id` or
            `self.data['data_mart_pk']`, default: None
        '''
        return serializers.IntegerField().to_internal_value(value)

    @cached_property
    def data_mart(self):
        '''
        :return: active `DataMartModel` instance from `self.data_mart_id`
        '''
        if self._data_mart is not None:
            return self._data_mart

        pk = self.data_mart_id
        if pk is not None:
            return get_object_or_404(DataMartModel.objects.active(), pk=pk)
        return None

    @cached_property
    def data_mart_term_ids(self):
        return self.data_mart.active_terms_ids if self.data_mart else []

    def filter_data_mart_pk(self, name, queryset, value):
        msg = "Method filter_data_mart_pk() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @cached_property
    @get_from_underscore_or_data('use_cached_decompress', True)
    def use_cached_decompress(self, value):
        '''
        :return: `use_cached_decompress` value parse from `self._use_cached_decompress` or
            `self.data['use_cached_decompress']`, default: True
        '''
        return serializers.BooleanField().to_internal_value(value)


_COMPARISONS_LABELS = {
    'exact': _('equal'),
    'lt': _('less than'),
    'lte': _('less than or equal'),
    'gt': _('greater than'),
    'gte': _('greater than or equal'),
    'date_range': _('date range')
}

_FIELDS_LABELS = {
    'created_at': _("Created at"),
    'updated_at': _("Updated at"),
}

def _format_label(*args):
    return '{} ({})'.format(*args)


class EntityFilter(BaseEntityFilter):
    """
    EntityFilter
    """
    id__in = NumberInFilter(name='id', label=_("IDs"))
    active = filters.MethodFilter(label=_("Active"))
    subj = filters.MethodFilter(widget=CSVWidget(), label=_("Subjects"))
    rel = filters.MethodFilter(widget=CSVWidget(), label=_("Relations"))
    created_at = filters.IsoDateTimeFilter(name='created_at', lookup_expr='exact', label=_format_label(
        _FIELDS_LABELS['created_at'], _COMPARISONS_LABELS['exact']))
    created_at__date_range = filters.DateRangeFilter(name='created_at', label=_format_label(
        _FIELDS_LABELS['created_at'], _COMPARISONS_LABELS['date_range']))
    created_at__lt = filters.IsoDateTimeFilter(name='created_at', lookup_expr='lt', label=_format_label(
        _FIELDS_LABELS['created_at'], _COMPARISONS_LABELS['lt']))
    created_at__lte = filters.IsoDateTimeFilter(name='created_at', lookup_expr='lte', label=_format_label(
        _FIELDS_LABELS['created_at'], _COMPARISONS_LABELS['lte']))
    created_at__gt = filters.IsoDateTimeFilter(name='created_at', lookup_expr='gt', label=_format_label(
        _FIELDS_LABELS['created_at'], _COMPARISONS_LABELS['gt']))
    created_at__gte = filters.IsoDateTimeFilter(name='created_at', lookup_expr='gte', label=_format_label(
        _FIELDS_LABELS['created_at'], _COMPARISONS_LABELS['gte']))
    updated_at = filters.IsoDateTimeFilter(name='updated_at', lookup_expr='exact', label=_format_label(
        _FIELDS_LABELS['updated_at'], _COMPARISONS_LABELS['exact']))
    updated_at__date_range = filters.DateRangeFilter(name='updated_at', label=_format_label(
        _FIELDS_LABELS['updated_at'], _COMPARISONS_LABELS['date_range']))
    updated_at__lt = filters.IsoDateTimeFilter(name='updated_at', lookup_expr='lt', label=_format_label(
        _FIELDS_LABELS['updated_at'], _COMPARISONS_LABELS['lt']))
    updated_at__lte = filters.IsoDateTimeFilter(name='updated_at', lookup_expr='lte', label=_format_label(
        _FIELDS_LABELS['updated_at'], _COMPARISONS_LABELS['lte']))
    updated_at__gt = filters.IsoDateTimeFilter(name='updated_at', lookup_expr='gt', label=_format_label(
        _FIELDS_LABELS['updated_at'], _COMPARISONS_LABELS['gt']))
    updated_at__gte = filters.IsoDateTimeFilter(name='updated_at', lookup_expr='gte', label=_format_label(
        _FIELDS_LABELS['updated_at'], _COMPARISONS_LABELS['gte']))

    class Meta:
        model = BaseEntity
        fields = {}

    def patch_data(self, data, **kwargs):
        data.update({
            '_initial_queryset': kwargs['queryset'],
            '_subj_ids': []
        })
        super(EntityFilter, self).patch_data(data, **kwargs)

    @cached_property
    @get_from_underscore_or_data('active', None)
    def is_active(self, value):
        '''
        :return: `is_active` value parse from `self._active` or
            `self.data['active']`, default: None
        '''
        return serializers.BooleanField().to_internal_value(value)

    def filter_active(self, name, queryset, value):
        self._is_active = value
        if self.is_active is None:
            return queryset
        if self.is_active:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].active()
            queryset = queryset.active()
        else:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].unactive()
            queryset = queryset.unactive()
        return queryset

    @cached_property
    def data_mart_rel_ids(self):
        return ['{}{}'.format(relation.term_id, relation.direction) for relation in
                self.data_mart.relations.all()] if self.data_mart else []

    def filter_data_mart_pk(self, name, queryset, value):
        self._data_mart_id = value
        if self.data_mart_id is None:
            return queryset
        self.data['_data_mart'] = self.data_mart
        if 'rel' not in self.data:
            rel_ids = self.data_mart_rel_ids
            if rel_ids:
                queryset = self.filter_rel(name, queryset, rel_ids)
        self.data['_initial_queryset'] = initial_queryset = self.data['_initial_queryset'].semantic_filter(
            self.data_mart_term_ids, use_cached_decompress=self.use_cached_decompress)
        self.data['_initial_filter_meta'] = initial_queryset.semantic_filter_meta
        if 'terms' in self.data:
            return queryset
        queryset = queryset.semantic_filter(self.data_mart_term_ids, use_cached_decompress=self.use_cached_decompress)
        self.data['_terms_filter_meta'] = queryset.semantic_filter_meta
        return queryset

    def filter_terms(self, name, queryset, value):
        self._term_ids = value
        if not self.term_ids:
            return queryset
        self.data['_terms_ids'] = self.term_ids
        selected = self.term_ids[:]
        selected.extend(self.data_mart_term_ids)
        queryset = queryset.semantic_filter(selected, use_cached_decompress=self.use_cached_decompress)
        self.data['_terms_filter_meta'] = queryset.semantic_filter_meta
        return queryset

    @cached_property
    @get_from_underscore_or_data('subj', [], lambda value: urllib.unquote(value).decode('utf8').split(","))
    def subj_ids(self, value):
        '''
        :return: `subj_ids` value parse from `self._subj_ids` or `self.data['subj']`, default: []
        '''
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)

    def filter_subj(self, name, queryset, value):
        self._subj_ids = value
        if not self.subj_ids:
            return queryset
        self.data['_subj_ids'] = self.subj_ids
        if self.rel_ids is None:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].subj(self.subj_ids)
            return queryset.subj(self.subj_ids)
        else:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].subj_and_rel(self.subj_ids, *self.rel_ids)
            return queryset.subj_and_rel(self.subj_ids, *self.rel_ids)

    @staticmethod
    def _separate_rel_by_key(rel, key, lst):
        i = rel.find(key)
        if i != -1:
            lst.append(int(rel[:i] + rel[i + 1:]))
            return True
        else:
            return False

    @cached_property
    @get_from_underscore_or_data('rel', None, lambda value: urllib.unquote(value).decode('utf8').split(","))
    def rel_ids(self, value):
        """
        `value` - raw relations list
        raw relation item: `id` + `direction`
        direction:
            "b", "" - bidirectional
            "f" - forward
            "r" - reverse
        :return: `relations` ([forward...], [reverse...])
        value parse from `self._rel_ids` or `self.data['rel']`, default: None
        """
        raw_rel = serializers.ListField(child=serializers.RegexField(r'^\d+[bfr]?$')).to_internal_value(value)
        rel_b_ids, rel_f_ids, rel_r_ids = [], [], []
        for x in raw_rel:
            if not EntityFilter._separate_rel_by_key(x, 'b', rel_b_ids):
                if not EntityFilter._separate_rel_by_key(x, 'f', rel_f_ids):
                    if not EntityFilter._separate_rel_by_key(x, 'r', rel_r_ids):
                        rel_b_ids.append(int(x))
        if rel_b_ids:
            rel_f_ids.extend(rel_b_ids)
            rel_r_ids.extend(rel_b_ids)
        return rel_f_ids, rel_r_ids

    def filter_rel(self, name, queryset, value):
        self._rel_ids = value
        if self.rel_ids is None or 'subj' in self.data:
            return queryset

        self.data['_initial_queryset'] = self.data['_initial_queryset'].rel(*self.rel_ids)
        return queryset.rel(*self.rel_ids)


class EntityMetaFilter(BaseFilterBackend):

    template = 'edw/entities/filters/meta.html'

    def filter_queryset(self, request, queryset, view):

        data_mart = request.GET['_data_mart']

        # annotation & aggregation
        annotation_meta, aggregation_meta = None, None
        if view.action == 'list':
            entity_model = data_mart.entities_model if data_mart is not None else queryset.model

            annotation = entity_model.get_summary_annotation()
            if isinstance(annotation, dict):
                annotation_meta, annotate_kwargs = {}, {}
                for key, value in annotation.items():
                    if isinstance(value, (tuple, list)):
                        annotate_kwargs[key] = value[0]
                        if len(value) > 1:
                            field = value[1]
                            if isinstance(field, six.string_types):
                                field = import_string(field)()
                            annotation_meta[key] = field
                    else:
                        annotate_kwargs[key] = value
                if annotate_kwargs:
                    queryset = queryset.annotate(**annotate_kwargs)

            aggregation = entity_model.get_summary_aggregation()
            if isinstance(aggregation, dict):
                aggregation_meta = {}
                for key, value in aggregation.items():
                    assert isinstance(value, (tuple, list)), (
                        "type of value getting from dictionary key '%s' should be `tuple` or `list`"
                        % key
                    )
                    aggregate = value[0]
                    n = len(value)
                    if n > 1:
                        field = value[1]
                        if isinstance(field, six.string_types):
                            field = import_string(field)()
                        name = value[2] if n > 2 else None
                    else:
                        field, name = None, None
                    aggregation_meta[key] = (aggregate, field, name)

        request.GET['_annotation_meta'] = annotation_meta
        request.GET['_aggregation_meta'] = aggregation_meta
        request.GET['_filter_queryset'] = queryset

        # select view component
        raw_view_component = request.GET.get('view_component', None)
        if raw_view_component is None:
            view_component = data_mart.view_component if data_mart is not None else None
        else:
            view_component = serializers.CharField().to_internal_value(raw_view_component)
        request.GET['_view_component'] = view_component

        return queryset

    def to_html(self, request, queryset, view):
        data_mart = request.GET.get('_data_mart', None)

        # annotation & aggregation
        annotation_meta, aggregation_meta = [], []
        if view.action == 'list':
            entity_model = data_mart.entities_model if data_mart is not None else queryset.model

            annotation = entity_model.get_summary_annotation()
            if isinstance(annotation, dict):
                annotation_meta = annotation.keys()

            aggregation = entity_model.get_summary_aggregation()
            if isinstance(aggregation, dict):
                aggregation_meta = [key for key, value in aggregation.items() if isinstance(value[0], BaseExpression)]

        context = {
            'annotation_meta': annotation_meta,
            'aggregation_meta': aggregation_meta
        }
        template = loader.get_template(self.template)
        return template_render(template, context)


class EntityDynamicFilterSet(DynamicFilterSetMixin, filters.FilterSet):

    class Meta:
        model = BaseEntity
        fields = {}


class EntityDynamicFilter(DynamicFilterMixin, BaseFilterBackend):

    dynamic_filter_set_class = EntityDynamicFilterSet

    template = 'edw/entities/filters/dynamic.html'

    def to_html(self, request, queryset, view):
        dynamic_filter_set = self.dynamic_filter_set_class(request.GET, queryset)
        rest_meta = getattr(dynamic_filter_set, '_rest_meta', None)
        if view.action == 'list' and rest_meta is not None and rest_meta.filters:
            for filter_name in rest_meta.filters.keys():
                dynamic_filter_set.data.setdefault(filter_name, '')
            context = {
                'form': dynamic_filter_set.form
            }
            template = loader.get_template(self.template)
            return template_render(template, context)
        return ''


class EntityGroupByFilter(BaseFilterBackend):

    like_param = 'like'

    template = 'edw/entities/filters/group_by.html'

    def get_like_param(self, request):
        param = request.query_params.get(self.like_param, None)
        if param is not None:
            return serializers.IntegerField().to_internal_value(param)
        return None

    def get_like(self, request, queryset):
        param = self.get_like_param(request)
        if param is not None:
            try:
                return queryset.filter(pk=param)[0]
            except IndexError:
                raise Http404
        return None

    def get_group_by(self, request, queryset):
        data_mart = request.GET['_data_mart']
        entity_model = data_mart.entities_model if data_mart is not None else queryset.model
        return entity_model._rest_meta.group_by

    def filter_queryset(self, request, queryset, view):
        group_by = []
        if view.action == 'list':
            group_by = self.get_group_by(request, queryset)
            if group_by:
                like = self.get_like(request, queryset.values(*group_by))
                if like is not None:
                    queryset = queryset.filter(**like)

                queryset_with_counts = queryset.group_by(*group_by)
                if queryset_with_counts.count() > 1:
                    queryset = queryset_with_counts
                else:
                    group_by = []

        request.GET['_group_by'] = group_by
        return queryset

    def to_html(self, request, queryset, view):
        if view.action == 'list':
            group_by = self.get_group_by(request, queryset)
            if group_by:
                like = self.get_like_param(request)
                context = {
                    'like': like if like is not None else '',
                    'group_by': group_by,
                    'like_param': self.like_param
                }
                template = loader.get_template(self.template)
                return template_render(template, context)
        return ''


class EntityOrderingFilter(OrderingFilter):

    def get_ordering(self, request, queryset, view):
        data_mart = request.GET['_data_mart']
        if data_mart is not None:
            self._extra_ordering = data_mart.entities_model.ORDERING_MODES
            setattr(view, 'ordering', data_mart.ordering.split(','))
        result = super(EntityOrderingFilter, self).get_ordering(request, queryset, view)
        request.GET['_ordering'] = result
        return result

    def get_valid_fields(self, queryset, view):
        result = super(EntityOrderingFilter, self).get_valid_fields(queryset, view)
        extra_ordering = getattr(self, '_extra_ordering', None)
        if extra_ordering is not None:
            fields = dict(result)
            valid_fields = []
            for item in extra_ordering:
                valid_fields.extend([(x.lstrip('-'), item[1]) for x in item[0].split(',')])
            fields.update(dict(valid_fields))
            result = fields.items()
        return result


