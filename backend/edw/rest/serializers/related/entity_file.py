# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from edw.models.related import EntityFileModel
from edw.rest.serializers.filer_fields import FilerFileField


class EntityFileSerializer(serializers.ModelSerializer):
    """
    Common serializer for the EntityFile model.
    """
    file = FilerFileField(max_length=None, use_url=True, upload_folder_name=_('Entities files'))
    file_serial = serializers.SerializerMethodField()
    original_filename = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = EntityFileModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}
        fields = '__all__'

    def get_file_size(self, instance):
        return instance.file._file_size

    def get_original_filename(self, instance):
        return instance.file.original_filename

    def get_file_serial(self, instance):
        return str(instance.file.file)

    def get_name(self, instance):
        return u'{}'.format(instance.file.name) if instance.file.name else ""

    def get_description(self, instance):
        return u'{}'.format(instance.file.description) if instance.file.description else ""