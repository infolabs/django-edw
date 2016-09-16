# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core import exceptions
from django.core.cache import cache
from django.template import RequestContext
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.utils.six import with_metaclass
from django.utils.html import strip_spaces_between_tags
from django.utils.safestring import mark_safe, SafeText
from django.utils.translation import get_language_from_request

from rest_framework import serializers

from edw import settings as edw_settings
from edw.models.entity import EntityModel


#===================================================


class EntityCommonSerializer(serializers.ModelSerializer):
    """
    Common serializer for the Entity model, both for the EntitySummarySerializer and the
    EntityDetailSerializer.
    """
    class Meta:
        model = EntityModel

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
        cache_key = 'entity:{0}|{1}-{2}-{3}-{4}-{5}'.format(entity.id, app_label, self.label, entity.entity_model,
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
            return SafeText("<!-- no such template: '{0}/entities/{1}-{2}-{3}.html' -->".format(*params[0]))
        # when rendering emails, we require an absolute URI, so that media can be accessed from
        # the mail client
        absolute_base_uri = request.build_absolute_uri('/').rstrip('/')
        context = RequestContext(request, {'entity': entity, 'ABSOLUTE_BASE_URI': absolute_base_uri})
        content = strip_spaces_between_tags(template.render(context).strip())
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
    entity_url = serializers.URLField(source='get_absolute_url', read_only=True)
    entity_type = serializers.CharField(read_only=True)
    entity_model = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'catalog')
        super(EntitySummarySerializerBase, self).__init__(*args, **kwargs)


class EntityDetailSerializerBase(EntityCommonSerializer):
    """
    Serialize all fields of the Product model, for the products detail view.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'catalog')
        super(EntityDetailSerializerBase, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        entity = super(EntityDetailSerializerBase, self).to_representation(obj)
        # add a serialized representation of the entity to the context
        return {'entity': dict(entity)}


class EntitySummarySerializer(EntitySummarySerializerBase):
    media = serializers.SerializerMethodField()

    class Meta(EntityCommonSerializer.Meta):
    # class Meta:
        # model = EntityModel
        fields = ('id', 'entity_name', 'entity_url', 'entity_model', 'media')

    def get_media(self, entity):
        return self.render_html(entity, 'media')


class EntityDetailSerializer(EntityDetailSerializerBase):
    class Meta(EntityCommonSerializer.Meta):
    # class Meta:
        # model = EntityModel
        exclude = ('active', 'polymorphic_ctype',)


#===================================================
'''
class AttributeSerializer(serializers.Serializer):
    """
    A serializer to convert the characteristics and marks for rendering.
    """
    name = serializers.CharField()
    path = serializers.CharField()
    values = serializers.ListField(child=serializers.CharField())
    view_class = serializers.ListField(child=serializers.CharField())


class EntitySerializer(serializers.HyperlinkedModelSerializer):
    """
    A simple serializer to convert the entity items for rendering.
    """
    #active = serializers.BooleanField()
    entity_name = serializers.CharField(read_only=True)
    entity_model = serializers.CharField(read_only=True)

    characteristics = AttributeSerializer(read_only=True, many=True)
    marks = AttributeSerializer(read_only=True, many=True)

    class Meta:
        model = EntityModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}


class EntityDetailSerializer(EntitySerializer):
    """
    EntityDetailSerializer
    """
    class Meta(EntitySerializer.Meta):
        fields = ('id', 'entity_name', 'entity_model', 'url', 'created_at', 'updated_at', 'active',
                  'characteristics', 'marks')


class EntitySummarySerializer(EntitySerializer):
    """
    EntitySummarySerializer
    """
    short_characteristics = AttributeSerializer(read_only=True, many=True)
    short_marks = AttributeSerializer(read_only=True, many=True)

    class Meta(EntitySerializer.Meta):
        fields = ('id', 'entity_name', 'entity_model', 'url', 'active', 'short_characteristics', 'short_marks')

'''
