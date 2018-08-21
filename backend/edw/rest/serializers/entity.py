# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core import exceptions
from django.core.cache import cache
from django.db.models.expressions import BaseExpression
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.utils.six import with_metaclass
from django.utils.html import strip_spaces_between_tags
from django.utils.safestring import mark_safe, SafeText
from django.utils.translation import get_language_from_request
from django.utils.functional import cached_property

from django.apps import apps

from rest_framework import serializers
from rest_framework.reverse import reverse

from edw import settings as edw_settings
from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.models.rest import (
    DynamicFieldsSerializerMixin,
    DynamicCreateUpdateValidateSerializerMixin,
    CheckPermissionsSerializerMixin
)
from edw.rest.serializers.data_mart import DataMartCommonSerializer, DataMartDetailSerializer
from edw.rest.serializers.decorators import empty


class AttributeSerializer(serializers.Serializer):
    """
    A serializer to convert the characteristics and marks for rendering.
    """
    name = serializers.CharField()
    path = serializers.CharField()
    values = serializers.ListField(child=serializers.CharField())
    view_class = serializers.ListField(child=serializers.CharField())


class EntityCommonSerializer(CheckPermissionsSerializerMixin, serializers.ModelSerializer):
    """
    Common serializer for the Entity model, both for the EntitySummarySerializer and the
    EntityDetailSerializer.
    """
    entity_model = serializers.CharField(read_only=True)
    entity_name = serializers.CharField(read_only=True)

    class Meta:
        model = EntityModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}

    HTML_SNIPPET_CACHE_KEY_PATTERN = 'entity:{0}|{1}-{2}-{3}-{4}-{5}'

    def render_html(self, entity, postfix):
        """
        Return a HTML snippet containing a rendered summary for this entity.
        Build a template search path with `postfix` distinction.
        """
        if not self.label:
            msg = "The Entity Serializer must be configured using a `label` field."
            raise exceptions.ImproperlyConfigured(msg)
        app_label = entity._meta.app_label.lower()
        request = self.context['request']
        cache_key = self.HTML_SNIPPET_CACHE_KEY_PATTERN.format(entity.id, app_label, self.label, entity.entity_model,
                                                            postfix, get_language_from_request(request))
        content = cache.get(cache_key)
        if content:
            return mark_safe(content)
        params = [
            (app_label, self.label, entity.entity_model, postfix),
            (app_label, self.label, 'entity', postfix),
            ('edw', self.label, 'entity', postfix),
        ]
        try:
            template = select_template(['{0}/entities/{1}-{2}-{3}.html'.format(*p) for p in params])
        except TemplateDoesNotExist:
            return SafeText("<!-- no such template: `{0}/entities/{1}-{2}-{3}.html` -->".format(*params[0]))
        # when rendering emails, we require an absolute URI, so that media can be accessed from
        # the mail client
        absolute_base_uri = request.build_absolute_uri('/').rstrip('/')
        context = {
            'entity': entity,
            'ABSOLUTE_BASE_URI': absolute_base_uri
        }
        data_mart = self.context.get('data_mart', None)
        if data_mart is not None:
            context['data_mart'] = data_mart
        content = strip_spaces_between_tags(template.render(context, request).strip())
        cache.set(cache_key, content, edw_settings.CACHE_DURATIONS['entity_html_snippet'])
        return mark_safe(content)


class SerializerRegistryMetaclass(serializers.SerializerMetaclass):
    """
    Keep a global reference onto the class implementing `EntitySummarySerializerBase`.
    There can be only one class instance, because the entities summary is the lowest common
    denominator for all entities of this edw instance. Otherwise we would be unable to mix
    different polymorphic entity types in the all list views.
    """
    def __new__(cls, clsname, bases, attrs):
        global entity_summary_serializer_class
        if entity_summary_serializer_class:
            msg = "Class `{}` inheriting from `EntitySummarySerializerBase` already registred."
            raise exceptions.ImproperlyConfigured(msg.format(entity_summary_serializer_class.__name__))
        new_class = super(cls, SerializerRegistryMetaclass).__new__(cls, clsname, bases, attrs)
        if clsname != 'EntitySummarySerializerBase':
            entity_summary_serializer_class = new_class
        return new_class

entity_summary_serializer_class = None


class EntitySummarySerializerBase(with_metaclass(SerializerRegistryMetaclass, EntityCommonSerializer)):
    """
    Serialize a summary of the polymorphic Entity model, suitable for Catalog List Views and other Views.
    """
    entity_url = serializers.SerializerMethodField()
    entity_type = serializers.CharField(read_only=True)

    short_characteristics = AttributeSerializer(read_only=True, many=True)
    short_marks = AttributeSerializer(read_only=True, many=True)

    extra = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'summary')
        super(EntitySummarySerializerBase, self).__init__(*args, **kwargs)

    def to_representation(self, data):
        """
        Prepare some data for serialization
        """
        if self.group_by:
            group_size = getattr(data, self.group_size_alias)
            if group_size > 1:
                queryset = self.context['filter_queryset']
                group_queryset = queryset.like(data.id, *self.group_by)

                # patch short_characteristics & short_marks
                data.short_characteristics = group_queryset.short_characteristics
                data.short_marks = group_queryset.short_marks

        return super(EntitySummarySerializerBase, self).to_representation(data)

    @cached_property
    def group_size_alias(self):
        return self.Meta.model.objects.queryset_class.GROUP_SIZE_ALIAS

    @cached_property
    def group_by(self):
        return self.context.get('group_by', [])

    def get_entity_url(self, instance):
        return instance.get_absolute_url(request=self.context.get('request'), format=self.context.get('format'))

    def get_extra(self, instance):
        extra = instance.get_summary_extra(self.context)

        annotation_meta = self.context.get('annotation_meta', None)

        if self.group_by:
            extra[self.group_size_alias] = getattr(instance, self.group_size_alias)
        elif annotation_meta:
            annotation = {}
            for key, field in annotation_meta.items():

                if field == field.root:
                    field.root = self.root

                value = getattr(instance, key)
                annotation[key] = field.to_representation(value) if value is not None else None

            if extra is not None:
                extra.update(annotation)
            else:
                extra = annotation

        return extra


class RelatedDataMartSerializer(DataMartCommonSerializer):
    entities_url = serializers.SerializerMethodField()
    is_subjective = serializers.SerializerMethodField()

    class Meta(DataMartCommonSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'data_mart_url', 'data_mart_model', 'is_leaf',
              'active', 'view_class', 'short_description', 'is_subjective', 'entities_url')

    def get_entities_url(self, instance):
        request = self.context.get('request', None)

        kwargs = {
            'data_mart_pk': instance.id
        }
        if instance.is_subjective:
            kwargs['entity_pk'] = self.entity_pk
            view_name = "edw:data-mart-entity-by-subject-list"
        else:
            view_name = "edw:data-mart-entity-list"

        format = self.context.get('format', None)
        return reverse(view_name, request=request, kwargs=kwargs, format=format)

    @property
    def entity_pk(self):
        return self.context.get('_entity_pk')

    def get_is_subjective(self, instance):
        return instance.is_subjective


class EntityDetailSerializerBase(DynamicFieldsSerializerMixin,
                                 DynamicCreateUpdateValidateSerializerMixin,
                                 EntityCommonSerializer):
    """
    Serialize all fields of the Entity model, for the entities detail view.
    """
    characteristics = AttributeSerializer(read_only=True, many=True)
    marks = AttributeSerializer(read_only=True, many=True)
    related_data_marts = serializers.SerializerMethodField()

    _meta_cache = {}

    @staticmethod
    def _get_meta_class(base, model_class):

        class Meta(base):
            model = model_class

        return Meta

    @classmethod
    def _update_meta(cls, it, model_class):
        key = model_class.__name__
        meta_class = cls._meta_cache.get(key, None)
        if meta_class is None:
            cls._meta_cache[key] = meta_class = EntityDetailSerializerBase._get_meta_class(it.Meta, model_class)
        setattr(it, 'Meta', meta_class)

    def __new__(cls, *args, **kwargs):
        it = super(EntityDetailSerializerBase, cls).__new__(cls, *args, **kwargs)
        if args:
            cls._update_meta(it, args[0].__class__)
        else:
            data = kwargs.get('data', None)
            if data is not None:
                context = kwargs.get('context', None)
                if context is not None:
                    request = context['request']
                    data_mart_pk = request.GET.get('data_mart_pk', None)
                    if data_mart_pk is not None:
                        # try find data_mart in cache
                        data_mart = request.GET.get('_data_mart', None)
                        if data_mart is not None and isinstance(data_mart, DataMartModel):
                            cls._update_meta(it, data_mart.entities_model)
                        else:
                            try:
                                data_mart = DataMartModel.objects.active().get(pk=data_mart_pk)
                            except DataMartModel.DoesNotExist:
                                pass
                            else:
                                cls._update_meta(it, data_mart.entities_model)
                    else:
                        entity_model = data.get('entity_model', None)
                        if entity_model is not None:
                            try:
                                model_class = apps.get_model(it.Meta.model._meta.app_label, str(entity_model))
                            except LookupError:
                                pass
                            else:
                                cls._update_meta(it, model_class)
        return it

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'detail')
        super(EntityDetailSerializerBase, self).__init__(*args, **kwargs)

    def to_representation(self, data):
        """
        Prepare some data for serialization
        """
        self.context['_entity_pk'] = data.id
        return super(EntityDetailSerializerBase, self).to_representation(data)

    def get_related_data_marts(self, entity):
        ids = entity.get_related_data_marts_ids_from_attributes(entity.marks, entity.characteristics)
        data_marts0 = entity.related_data_marts.active()

        if ids:
            data_marts0 = list(data_marts0)
            data_marts1 = list(DataMartModel.objects.active().filter(id__in=ids))

            data_marts = []
            while data_marts0 and data_marts1:
                if data_marts0[0] == data_marts1[0]:
                    data_marts.append(data_marts1.pop(0))
                    data_marts0.pop(0)
                elif data_marts0[0] < data_marts1[0]:
                    data_marts.append(data_marts0.pop(0))
                else:
                    data_marts.append(data_marts1.pop(0))
            if data_marts0:
                data_marts.extend(data_marts0)
            elif data_marts1:
                data_marts.extend(data_marts1)
        else:
            data_marts = data_marts0

        related_data_mart_serializer = RelatedDataMartSerializer(data_marts, context=self.context, many=True)
        return related_data_mart_serializer.data


class EntitySummarySerializer(EntitySummarySerializerBase):
    media = serializers.SerializerMethodField()

    class Meta(EntityCommonSerializer.Meta):
        fields = ('id', 'entity_name', 'entity_url', 'entity_model',
                  'short_characteristics', 'short_marks', 'media', 'extra')

    def get_media(self, entity):
        return self.render_html(entity, 'media')


class EntityDetailSerializer(EntityDetailSerializerBase):
    media = serializers.SerializerMethodField()

    class Meta(EntityCommonSerializer.Meta):

        exclude = ('active', 'polymorphic_ctype', 'additional_characteristics_or_marks', '_relations', 'terms')

    def get_media(self, entity):
        return self.render_html(entity, 'media')


class EntitySummaryMetadataSerializer(serializers.Serializer):
    data_mart = serializers.SerializerMethodField()
    terms_ids = serializers.SerializerMethodField()
    subj_ids = serializers.SerializerMethodField()
    ordering = serializers.SerializerMethodField()
    view_component = serializers.SerializerMethodField()
    aggregation = serializers.SerializerMethodField()
    group_by = serializers.SerializerMethodField()
    potential_terms_ids = serializers.SerializerMethodField()
    real_terms_ids = serializers.SerializerMethodField()
    extra = serializers.SerializerMethodField()

    @staticmethod
    def on_terms_ids_cache_set(key):
        buf = EntityModel.get_terms_cache_buffer()
        old_key = buf.record(key)
        if old_key != buf.empty:
            cache.delete(old_key)

    def get_potential_terms_ids(self, instance):
        tree = self.context['initial_filter_meta']
        initial_queryset = self.context['initial_queryset']
        return initial_queryset.get_terms_ids(tree).cache(on_cache_set=self.on_terms_ids_cache_set,
                                                          timeout=EntityModel.TERMS_IDS_CACHE_TIMEOUT)

    def _get_cached_real_terms_ids(self, instance):
        real_terms_ids = getattr(self, '_cached_real_terms_ids', None)
        if real_terms_ids is None:
            tree = self.context['terms_filter_meta']
            filter_queryset = self.context['filter_queryset']
            real_terms_ids = self._cached_real_terms_ids = filter_queryset.get_terms_ids(tree).cache(
                on_cache_set=self.on_terms_ids_cache_set, timeout=EntityModel.TERMS_IDS_CACHE_TIMEOUT)
        return real_terms_ids

    def get_terms_ids(self, instance):
        return self.context['terms_ids']

    def get_real_terms_ids(self, instance):
        return self._get_cached_real_terms_ids(instance)

    def get_data_mart(self, instance):
        data_mart = self.context['data_mart']
        self.context.update({
            'real_terms_ids': self._get_cached_real_terms_ids(instance)
        })
        if data_mart is not None:
            serializer = DataMartDetailSerializer(data_mart, context=self.context)
            return serializer.data
        return None

    def get_subj_ids(self, instance):
        return self.context['subj_ids']

    def get_ordering(self, instance):
        ordering = self.context['ordering']
        return ",".join(ordering) if ordering else None

    def get_view_component(self, instance):
        return self.context['view_component']

    def get_extra(self, instance):
        return self.context.get('extra', None)

    def get_aggregation(self, instance):
        aggregation_meta = self.context['aggregation_meta']
        if aggregation_meta:
            aggregate_kwargs = dict([(key, value[0]) for key, value in aggregation_meta.items()
                                     if isinstance(value[0], BaseExpression)])
            queryset = self.context['filter_queryset']
            aggregation = queryset.aggregate(**aggregate_kwargs)
            result = {}
            name_field = serializers.CharField()
            for key, data in aggregation_meta.items():
                field = data[1]
                if field is not None:
                    if field == field.root:
                        field.root = self.root
                    name = data[2]
                    value = aggregation.get(key, empty)
                    if value == empty:
                        alias = data[0]
                        value = [aggregation[x] for x in alias] if isinstance(alias, (tuple, list)
                                                                              ) else aggregation[alias]
                    result[key] = {
                        'value': field.to_representation(value) if value is not None else None,
                        'name': name_field.to_representation(name) if name is not None else None
                    }
            return result
        else:
            return None

    def get_group_by(self, instance):
        return self.context['group_by']


class EntityTotalSummarySerializer(serializers.Serializer):
    meta = EntitySummaryMetadataSerializer(source="*")
    objects = EntitySummarySerializer(source="*", many=True)

    def __new__(cls, *args, **kwargs):
        kwargs['many'] = False
        return super(EntityTotalSummarySerializer, cls).__new__(cls, *args, **kwargs)
