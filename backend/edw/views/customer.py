# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters

from edw.models.customer import CustomerModel
from edw.rest.serializers.customer import CustomerSerializer
from edw.rest.viewsets import remove_empty_params_from_request


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving customer.
    """
    queryset = CustomerModel.objects.all()
    serializer_class = CustomerSerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('first_name', 'last_name')
    ordering_fields = ('first_name', )

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(CustomerViewSet, self).initialize_request(*args, **kwargs)

