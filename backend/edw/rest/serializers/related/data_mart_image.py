# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from edw.models.related.data_mart_image import DataMartImageModel

from edw.rest.serializers.filer_fields import FilerImageField


class DataMartImageSerializer(serializers.ModelSerializer):
    """
    Common serializer for the DataMartImage model.
    """
    image = FilerImageField(max_length=None, use_url=True, upload_folder_name=_('Data marts images'))
    original_filename = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = DataMartImageModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}
        fields = '__all__'

    def get_file_size(self, instance):
        return instance.image._file_size

    def get_original_filename(self, instance):
        return instance.image.original_filename
