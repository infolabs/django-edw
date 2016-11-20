# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers

from edw.models.related import DataMartImageModel

from edw.rest.serializers.filer_fields import FilerImageField


class DataMartImageSerializer(serializers.ModelSerializer):
    """
    Common serializer for the DataMartImage model.
    """
    image = FilerImageField(max_length=None, use_url=True, upload_folder_name=_('Data marts images'))

    class Meta:
        model = DataMartImageModel
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}
        fields = '__all__'