# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from edw.models.related.entity_image import EntityImageModel
from edw.rest.serializers.filer_fields import FilerImageField


class EntityImageSerializer(serializers.ModelSerializer):
    """
    Common serializer for the EntityImage model.
    """
    image = FilerImageField(max_length=None, use_url=True, upload_folder_name=_('Entities images'))
    file = serializers.SerializerMethodField()
    original_filename = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    default_caption = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    subject_location = serializers.SerializerMethodField()

    class Meta:
        model = EntityImageModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}
        fields = '__all__'

    def get_file_size(self, instance):
        return instance.image._file_size

    def get_original_filename(self, instance):
        return instance.image.original_filename

    def get_file(self, instance):
        return str(instance.image.file)

    def get_author(self, instance):
        return u'{}'.format(instance.image.author) if instance.image.author else ""

    def get_name(self, instance):
        return u'{}'.format(instance.image.name) if instance.image.name else ""

    def get_default_caption(self, instance):
        return u'{}'.format(instance.image.default_caption) if instance.image.default_caption else ""

    def get_alt(self, instance):
        return u'{}'.format(instance.image.default_alt_text) if instance.image.default_alt_text else ""

    def get_description(self, instance):
        return u'{}'.format(instance.image.description) if instance.image.description else ""

    def get_subject_location(self, instance):
        return u'{}'.format(instance.image.subject_location) if instance.image.subject_location else ""
