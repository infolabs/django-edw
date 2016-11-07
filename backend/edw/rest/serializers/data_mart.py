# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import types

from django.core import exceptions
from django.core.cache import cache
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.utils.functional import cached_property
from django.utils.six import with_metaclass
from django.utils.html import strip_spaces_between_tags
from django.utils.safestring import mark_safe, SafeText
from django.utils.translation import get_language_from_request

from rest_framework import serializers
from rest_framework_recursive.fields import RecursiveField

from edw import settings as edw_settings
from edw.models.data_mart import DataMartModel
from edw.rest.serializers.decorators import get_from_context_or_request


class DataMartCommonSerializer(serializers.ModelSerializer):
    """
    A simple serializer to convert the data mart items for rendering.
    """
    #name = serializers.CharField(read_only=True)
    #slug = serializers.SlugField(max_length=50, min_length=None, allow_blank=False)
    #path = serializers.CharField(max_length=255, allow_blank=False, read_only=True)
    #active = serializers.BooleanField()
    #description = serializers.CharField(read_only=True)
    #view_class = serializers.CharField(read_only=True)
    data_mart_model = serializers.CharField(read_only=True)
    parent_id = serializers.SerializerMethodField()

    class Meta:
        model = DataMartModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}

    def render_html(self, data_mart, postfix):
        """
        Return a HTML snippet containing a rendered summary for this data mart.
        Build a template search path with `postfix` distinction.
        """
        if not self.label:
            msg = "The DataMart Serializer must be configured using a `label` field."
            raise exceptions.ImproperlyConfigured(msg)
        app_label = data_mart._meta.app_label.lower()
        request = self.context['request']
        cache_key = 'data_mart:{0}|{1}-{2}-{3}-{4}-{5}'.format(data_mart.id, app_label, self.label,
                                                               data_mart.data_mart_model,
                                                               postfix, get_language_from_request(request))
        content = cache.get(cache_key)
        if content:
            return mark_safe(content)
        params = [
            (app_label, self.label, data_mart.data_mart_model, postfix),
            (app_label, self.label, 'data_mart', postfix),
            ('edw', self.label, 'data_mart', postfix),
        ]
        try:
            template = select_template(['{0}/data_marts/{1}-{2}-{3}.html'.format(*p) for p in params])
        except TemplateDoesNotExist:
            return SafeText("<!-- no such template: '{0}/data_marts/{1}-{2}-{3}.html' -->".format(*params[0]))
        # when rendering emails, we require an absolute URI, so that media can be accessed from
        # the mail client
        absolute_base_uri = request.build_absolute_uri('/').rstrip('/')
        context = {
            'data_mart': data_mart,
            'ABSOLUTE_BASE_URI': absolute_base_uri
        }
        content = strip_spaces_between_tags(template.render(context, request).strip())
        cache.set(cache_key, content, edw_settings.CACHE_DURATIONS['data_mart_html_snippet'])
        return mark_safe(content)

    def get_parent_id(self, instance):
        return instance.parent_id


class SerializerRegistryMetaclass(serializers.SerializerMetaclass):
    """
    Keep a global reference onto the class implementing `DataMartSummarySerializerBase`.
    There can be only one class instance, because the data marts summary is the lowest common
    denominator for all entities of this edw instance. Otherwise we would be unable to mix
    different polymorphic data mart types in the all list views.
    """
    def __new__(cls, clsname, bases, attrs):
        global data_mart_summary_serializer_class
        if data_mart_summary_serializer_class:
            msg = "Class `{}` inheriting from `DataMartSummarySerializerBase` already registred."
            raise exceptions.ImproperlyConfigured(msg.format(data_mart_summary_serializer_class.__name__))
        new_class = super(cls, SerializerRegistryMetaclass).__new__(cls, clsname, bases, attrs)
        if clsname != 'DataMartSummarySerializerBase':
            data_mart_summary_serializer_class = new_class
        return new_class

data_mart_summary_serializer_class = None


class DataMartDetailSerializerBase(DataMartCommonSerializer):
    """
    Serialize all fields of the DataMart model, for the data mart detail view.
    """
    entities_ordering_modes = serializers.SerializerMethodField()
    rel = serializers.SerializerMethodField()

    _meta_cache = {}

    @staticmethod
    def _get_meta_class(base, model_class):

        class Meta(base):
            model = model_class

        return Meta

    @classmethod
    def _update_meta(cls, it, instance):
        model_class = instance.__class__
        key = model_class.__name__
        meta_class = cls._meta_cache.get(key, None)
        if meta_class is None:
            cls._meta_cache[key] = meta_class = DataMartDetailSerializerBase._get_meta_class(it.Meta, model_class)
        setattr(it, 'Meta', meta_class)

    def __new__(cls, *args, **kwargs):
        it = super(DataMartDetailSerializerBase, cls).__new__(cls, *args, **kwargs)
        if args:
            cls._update_meta(it, args[0])
        return it

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'detail')
        instance = args[0] if args else None
        if instance is not None and hasattr(instance, '_rest_meta'):
            rest_meta = instance._rest_meta
        else:
            rest_meta = getattr(self.Meta.model, '_rest_meta', None)
        super(DataMartDetailSerializerBase, self).__init__(*args, **kwargs)
        if rest_meta:
            remove_fields, include_fields = rest_meta.exclude, rest_meta.include
            # for multiple fields in a list
            for field_name in remove_fields:
                self.fields.pop(field_name)
            for field_name, field in include_fields.items():
                if isinstance(field, serializers.SerializerMethodField):
                    default_method_name = 'get_{field_name}'.format(field_name=field_name)
                    if field.method_name is None:
                        method_name = default_method_name
                    else:
                        method_name = field.method_name
                        # hack for SerializerMethodField.bind method
                        if field.method_name == default_method_name:
                            field.method_name = None
                    method = getattr(rest_meta, method_name)
                    setattr(self, method_name, types.MethodType(method, self, self.__class__))
                self.fields[field_name] = field

    def get_entities_ordering_modes(self, instance):
        return dict(instance.ENTITIES_ORDERING_MODES)

    def get_rel(self, instance):
        return ['{}{}'.format(relation.term_id, relation.direction) for relation in instance.relations.all()]


class DataMartDetailSerializer(DataMartDetailSerializerBase):
    media = serializers.SerializerMethodField()

    class Meta(DataMartCommonSerializer.Meta): #todo: url!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        exclude = ('active', 'polymorphic_ctype', '_relations', 'terms') #todo: remove tree_id and e.t.!!!!!!

    def get_media(self, data_mart):
        return self.render_html(data_mart, 'media')


class DataMartSummarySerializerBase(with_metaclass(SerializerRegistryMetaclass, DataMartCommonSerializer)):
    """
    Serialize a summary of the polymorphic DataMart model.
    """
    data_mart_url = serializers.SerializerMethodField()
    data_mart_type = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'summary')
        super(DataMartSummarySerializerBase, self).__init__(*args, **kwargs)

    def get_data_mart_url(self, instance):
        return instance.get_absolute_url(request=self.context.get('request'), format=self.context.get('format'))


class DataMartSummarySerializer(DataMartSummarySerializerBase):
    media = serializers.SerializerMethodField()

    class Meta(DataMartCommonSerializer.Meta):
        fields = ('id', 'parent_id', 'name', 'slug', 'data_mart_url', 'data_mart_model',
                  'active', 'view_class', 'media')

    def get_media(self, data_mart):
        return self.render_html(data_mart, 'media')


class _DataMartFilterMixin(object):
    """
    If `active_only` parameter set `True`, then add filtering by `active` = `True`
    """
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
        buf = DataMartModel.get_children_buffer()
        old_key = buf.record(key)
        if old_key != buf.empty:
            cache.delete(old_key)

    def prepare_data(self, data):
        if self.cached:
            return data.cache(on_cache_set=_DataMartFilterMixin.on_cache_set,
                              timeout=DataMartModel.CHILDREN_CACHE_TIMEOUT)
        else:
            return data.prepare_for_cache(data)

    def to_representation(self, data):
        max_depth = self.max_depth
        next_depth = self.depth + 1
        if max_depth is not None and next_depth > max_depth:
            data_marts = []
        else:
            data_marts = self.prepare_data(self.active_only_filter(data))
            for data_mart in data_marts:
                data_mart._depth = next_depth
        return super(_DataMartFilterMixin, self).to_representation(data_marts)


class DataMartTreeListField(_DataMartFilterMixin, serializers.ListField):
    """
    DataMartTreeListField
    """
    @cached_property
    def depth(self):
        return self.parent._depth


class _DataMartTreeRootSerializer(_DataMartFilterMixin, serializers.ListSerializer):
    """
    Data Mart Tree Root Serializer
    """
    @cached_property
    def depth(self):
        return 0


class DataMartTreeSerializer(DataMartCommonSerializer): # todo: may be summury????!!!!!
    """
    Data Mart Tree Serializer
    """
    children = DataMartTreeListField(child=RecursiveField(), source='get_children', read_only=True)

    class Meta(DataMartCommonSerializer.Meta):
        fields = ('id', 'name', 'slug', 'active', 'view_class', 'children') #todo: url!!!!!!!!!!!!!!!!!!!!!
        list_serializer_class = _DataMartTreeRootSerializer

    def to_representation(self, data):
        """
        Prepare some data for children serialization
        """
        self._depth = data._depth
        return super(DataMartTreeSerializer, self).to_representation(data)
