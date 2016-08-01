# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from edw.models.customer import CustomerModel

class CustomerSerializer(serializers.HyperlinkedModelSerializer):
    salutation = serializers.CharField(source='get_salutation_display')

    class Meta:
        model = CustomerModel
        fields = ('salutation', 'first_name', 'last_name', 'email', 'extra', 'url')
        extra_kwargs = {'url': {'view_name': 'edw:{}-detail'.format(model._meta.model_name)}}
