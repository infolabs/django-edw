# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

import rest_framework_filters as filters
try:
    from rest_framework_filters import MethodFilter
except ImportError:
    from .common import MethodFilter

from django.apps import apps
from django.db.models.expressions import BaseExpression
from django.template import loader
from django.utils import six
from django.utils.functional import cached_property
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.filters import OrderingFilter, BaseFilterBackend


from edw.utils.common import template_render
from edw.models.data_mart import DataMartModel
from edw.models.entity import BaseEntity, EntityModel
from edw.models.rest import (
    DynamicFilterSetMixin,
    DynamicFilterMixin,
    DynamicGroupByMixin
)
from edw.models.term import TermModel
from edw.rest.filters.decorators import get_from_underscore_or_data
from edw.rest.filters.widgets import CSVWidget
from edw.utils.hash_helpers import get_data_mart_cookie_setting
from edw.views.generics import get_object_or_404

from .widgets import parse_query
from .common import NumberInFilter


class BaseEntityFilter(filters.FilterSet):
    """
    BaseEntityFilter
    """
    terms = MethodFilter(widget=CSVWidget(), label=_("Terms"))
    data_mart_pk = MethodFilter(label=_("Data mart"))

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
    @get_from_underscore_or_data('terms', [], parse_query)
    def term_ids(self, value):
        """
        :return: `term_ids` value parse from `self._term_ids` or `self.data['terms']`, default: []
        """
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)

    def filter_terms(self, name, queryset, value):
        msg = "Method filter_terms() must be implemented by subclass: `{}`"
        raise NotImplementedError(msg.format(self.__class__.__name__))

    @cached_property
    @get_from_underscore_or_data('data_mart_pk', None)
    def data_mart_id(self, value):
        """
        :return: `data_mart_id` value parse from `self._data_mart_id` or
            `self.data['data_mart_pk']`, default: None
        """
        return serializers.CharField().to_internal_value(value)

    @cached_property
    def data_mart(self):
        """
        :return: active `DataMartModel` instance from `self.data_mart_id`
        """
        if self._data_mart is not None:
            return self._data_mart

        value = self.data_mart_id
        if value is not None:
            key = 'pk'
            # it was a string, not an int. Try find object by `slug`
            try:
                value = int(value)
            except ValueError:
                key = 'slug'
            return get_object_or_404(DataMartModel.objects.active(), **{key: value})
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
        """
        :return: `use_cached_decompress` value parse from `self._use_cached_decompress` or
            `self.data['use_cached_decompress']`, default: True
        """
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
    active = MethodFilter(label=_("Active"))
    subj = MethodFilter(widget=CSVWidget(), label=_("Subjects"))
    rel = MethodFilter(widget=CSVWidget(), label=_("Relations"))
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
        """
        TRUE - 't', 'T', 'true', 'True', 'TRUE', '1', 1, True
        FALSE - 'f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False
        NULL - 'n', 'N', 'null', 'Null', 'NULL', '', None
        :return: `is_active` value parse from `self._active` or
            `self.data['active']`, default: None
        """
        return serializers.NullBooleanField().to_internal_value(value)

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
    def data_mart_relations(self):
        return list(self.data_mart.relations.all()) if self.data_mart else []

    @cached_property
    def is_data_mart_has_relations(self):
        return any(self.data_mart_relations)

    @cached_property
    def data_mart_relations_subjects(self):
        return DataMartModel.get_relations_subjects(self.data_mart_relations)

    @cached_property
    def is_data_mart_relations_has_subjects(self):
        return any(self.data_mart_relations_subjects.values())

    @cached_property
    def data_mart_rel_ids(self):
        return DataMartModel.separate_relations(self.data_mart_relations)

    def filter_data_mart_pk(self, name, queryset, value):
        self._data_mart_id = value
        if self.data_mart_id is None:
            return queryset
        self.data['_data_mart'] = self.data_mart

        if self.is_data_mart_has_relations and 'rel' not in self.data:
            # patch rel_ids
            self.rel_ids = self.data_mart_rel_ids
            queryset = self.filter_rel(name, queryset, None)

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
    @get_from_underscore_or_data('subj', [], parse_query)
    def subj_ids(self, value):
        """
        :return: `subj_ids` value parse from `self._subj_ids` or `self.data['subj']`, default: []
        """
        return serializers.ListField(child=serializers.IntegerField()).to_internal_value(value)

    @cached_property
    def rel_subj(self):
        """
        :return: `subj` value parse from `self.subj_ids` or dict of {relation: subject_ids...}
        """
        if self.is_data_mart_relations_has_subjects:
            if self.subj_ids:
                cleaned_relations_subjects = {}
                for rel_id, subj_ids in self.data_mart_relations_subjects.items():
                    if subj_ids:
                        cleaned_subj_ids = list(set(self.subj_ids) & set(subj_ids))
                        if not cleaned_subj_ids:
                            cleaned_subj_ids = subj_ids
                        cleaned_relations_subjects[rel_id] = cleaned_subj_ids
                    else:
                        cleaned_relations_subjects[rel_id] = self.subj_ids
                return cleaned_relations_subjects
            else:
                return self.data_mart_relations_subjects
        return self.subj_ids

    def filter_subj(self, name, queryset, value):
        self._subj_ids = value
        if not self.rel_subj:
            return queryset

        self.data['_subj_ids'] = self.subj_ids
        if self.rel_ids is None:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].subj(self.subj_ids)
            return queryset.subj(self.subj_ids)
        else:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].subj_and_rel(self.rel_subj, *self.rel_ids)
            return queryset.subj_and_rel(self.rel_subj, *self.rel_ids)

    @staticmethod
    def separate_rel_by_key(rel, key):
        i = rel.find(key)
        return int(rel[:i] + rel[i + 1:]) if i != -1 else None

    @cached_property
    @get_from_underscore_or_data('rel', None, parse_query)
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
            rel_id = EntityFilter.separate_rel_by_key(x, 'b')
            if rel_id is None:
                rel_id = EntityFilter.separate_rel_by_key(x, 'f')
                if rel_id is None:
                    rel_id = EntityFilter.separate_rel_by_key(x, 'r')
                    if rel_id is None:
                        rel_b_ids.append(int(x))
                    else:
                        rel_r_ids.append(rel_id)
                else:
                    rel_f_ids.append(rel_id)
            else:
                rel_b_ids.append(rel_id)

        if rel_b_ids:
            rel_f_ids.extend(rel_b_ids)
            rel_r_ids.extend(rel_b_ids)

        # Sanitize relations
        if self.is_data_mart_has_relations:
            rel_f_ids = list(set(rel_f_ids) & set(self.data_mart_rel_ids[0]))
            rel_r_ids = list(set(rel_r_ids) & set(self.data_mart_rel_ids[1]))
            if not any((rel_f_ids, rel_r_ids)):
                return self.data_mart_rel_ids

        return rel_f_ids, rel_r_ids

    def filter_rel(self, name, queryset, value):
        self._rel_ids = value
        if self.rel_ids is None or 'subj' in self.data:
            return queryset

        if self.is_data_mart_relations_has_subjects:
            # patch rel_subj
            self.rel_subj = self.data_mart_relations_subjects
            return self.filter_subj(name, queryset, [])
        else:
            self.data['_initial_queryset'] = self.data['_initial_queryset'].rel(*self.rel_ids)
            return queryset.rel(*self.rel_ids)


class EntityMetaFilter(BaseFilterBackend):

    alike_param = 'alike'

    template = 'edw/entities/filters/meta.html'

    def get_alike_param(self, request, view):
        param = request.query_params.get(self.alike_param, None)
        if param is not None:
            if view.action == 'list':
                return serializers.IntegerField().to_internal_value(param)
            elif view.action == 'retrieve':
                return True if serializers.BooleanField().to_internal_value(param) else None
        return None

    def filter_queryset(self, request, queryset, view):
        alike = self.get_alike_param(request, view)
        data_mart = request.GET['_data_mart']
        annotation_meta, aggregation_meta = None, None

        # annotation
        if view.action == 'list' or alike is not None:

            if alike is True:
                # Perform the lookup filtering.
                lookup_url_kwarg = view.lookup_url_kwarg or view.lookup_field
                assert lookup_url_kwarg in view.kwargs, (
                    'Expected view %s to be called with a URL keyword argument '
                    'named "%s". Fix your URL conf, or set the `.lookup_field` '
                    'attribute on the view correctly.' %
                    (view.__class__.__name__, lookup_url_kwarg)
                )
                filter_kwargs = {view.lookup_field: view.kwargs[lookup_url_kwarg]}
                obj = get_object_or_404(queryset, **filter_kwargs)
                model_class = obj.__class__
            else:
                model_class = data_mart.entities_model if data_mart is not None else queryset.model

            annotation = model_class.get_summary_annotation(request)
            if isinstance(annotation, dict):
                annotation_meta, annotate_kwargs = {}, {}
                for key, value in annotation.items():
                    if isinstance(value, (tuple, list)):
                        annotate = value[0]
                        if isinstance(annotate, BaseExpression):
                            annotate_kwargs[key] = annotate
                        n = len(value)
                        if n > 1:
                            field = value[1]
                            if isinstance(field, six.string_types):
                                field = import_string(field)()
                            name = value[2] if n > 2 else None
                            annotation_meta[key] = (annotate, field, name)
                    else:
                        assert isinstance(value, BaseExpression), (
            "value getting from dictionary key '%s' should be instance of a class or of a subclass `BaseExpression`"
                                % key
                        )
                        annotate_kwargs[key] = value
                if annotate_kwargs:
                    queryset = queryset.annotate(**annotate_kwargs)

        else:
            model_class = queryset.model

            if view.action in ("bulk_update", "partial_bulk_update"):
                if data_mart is not None:
                    model_class = data_mart.entities_model
                else:
                    # в случаи списка пытаемся определить модель по полю 'entity_model' первого элемента
                    if isinstance(request.data, list):
                        entity_model = request.data[0].get('entity_model', None) if len(request.data) else None
                    else:
                        entity_model = request.data.get('entity_model', None)
                    # пытаемся определить модель по параметру 'entity_model' словаря GET
                    if entity_model is None:
                        entity_model = request.GET.get('entity_model', None)
                    if entity_model is not None:
                        try:
                            model_class = apps.get_model(EntityModel._meta.app_label, str(entity_model))
                        except LookupError:
                            pass
                # modify queryset for `bulk_update` and `partial_bulk_update`
                queryset = model_class.objects.filter(id__in=queryset.values_list('id', flat=True))

        # aggregation
        if view.action == 'list':
            aggregation = model_class.get_summary_aggregation(request)
            if isinstance(aggregation, dict):
                aggregation_meta = OrderedDict()
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

        request.GET.update({
            '_annotation_meta': annotation_meta,
            '_aggregation_meta': aggregation_meta,
            '_filter_queryset': queryset,
            '_alike': alike,
            '_alike_param': self.alike_param,
            '_entity_model': model_class
        })

        # select view component
        raw_view_component = request.GET.get('view_component', None)
        if raw_view_component is None:
            raw_view_component = get_data_mart_cookie_setting(request, "view_component")
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
            model_class = data_mart.entities_model if data_mart is not None else queryset.model

            annotation = model_class.get_summary_annotation(request)
            if isinstance(annotation, dict):
                annotation_meta = list(annotation.keys())

            aggregation = model_class.get_summary_aggregation(request)
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


class EntityGroupByFilter(DynamicGroupByMixin, BaseFilterBackend):

    template = 'edw/entities/filters/group_by.html'

    def _get_group_by(self, request, queryset, view):
        self.initialize(request, queryset, view)
        return self.get_group_by()

    def filter_queryset(self, request, queryset, view):
        group_by = []
        if view.action == 'list':
            group_by = self._get_group_by(request, queryset, view)
            if group_by:
                alike_id = request.GET.get('_alike', None)
                if alike_id is not None:
                    queryset = queryset.alike(alike_id, *group_by)
                    # добавляем в информацию о фильтре
                    request.GET['_filter_queryset'] = queryset

                queryset_with_counts = queryset.group_by(*group_by)
                if queryset_with_counts.count() > 1:
                    queryset = queryset_with_counts
                else:
                    group_by = []
        elif view.action == 'retrieve':
            group_by = self._get_group_by(request, queryset, view)

        request.GET['_group_by'] = group_by
        return queryset

    def to_html(self, request, queryset, view):
        if view.action == 'list':
            group_by = self._get_group_by(request, queryset, view)
            if group_by:
                alike_id = request.GET.get('_alike')
                alike_param = request.GET.get('_alike_param')
                context = {
                    'alike': alike_id if alike_id is not None else '',
                    'group_by': group_by,
                    'alike_param': alike_param
                }
                template = loader.get_template(self.template)
                return template_render(template, context)
        return ''


class EntityOrderingFilter(OrderingFilter):

    def filter_queryset(self, request, queryset, view):
        if view.action in ("bulk_update", "partial_bulk_update"):
            return queryset
        return super(EntityOrderingFilter, self).filter_queryset(request, queryset, view)

    def get_ordering(self, request, queryset, view):
        ordering = get_data_mart_cookie_setting(request, "ordering")
        if ordering is not None:
            # %2C is an ASCII keycode in hexadecimal for a comma
            ordering = ordering.split("%2C")
        data_mart = request.GET['_data_mart']
        if data_mart is not None:
            self._extra_ordering = data_mart.entities_model.get_ordering_modes(context={'request': request})
            if ordering is None:
                ordering = data_mart.ordering.split(',')
        if ordering is not None:
            setattr(view, 'ordering', ordering)
        result = super(EntityOrderingFilter, self).get_ordering(request, queryset, view)
        request.GET['_ordering'] = result
        return result

    def get_valid_fields(self, queryset, view, context={}):
        result = super(EntityOrderingFilter, self).get_valid_fields(queryset, view)
        extra_ordering = getattr(self, '_extra_ordering', None)
        if extra_ordering is not None:
            fields = dict(result)
            valid_fields = []
            for item in extra_ordering:
                valid_fields.extend([(x.lstrip('-'), item[1]) for x in item[0].split(',')])
            fields.update(dict(valid_fields))
            result = list(fields.items())
        return result
