# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from edw.models.customer import CustomerModel

class CustomerSerializer(serializers.ModelSerializer):
    salutation = serializers.CharField(source='get_salutation_display')

    class Meta:
        model = CustomerModel
        fields = ('salutation', 'first_name', 'last_name', 'email', 'extra',)
