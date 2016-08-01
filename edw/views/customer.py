# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters

from edw.rest.serializers.customer import CustomerSerializer
from edw.models.customer import CustomerModel



class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving customer.
    """
    queryset = CustomerModel.objects.all()
    serializer_class = CustomerSerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    search_fields = ('first_name', 'last_name')
    ordering_fields = ('first_name', )

    def initialize_request(self, request, *args, **kwargs):
        """
        Remove empty query params from request
        """
        query_params = request.GET.copy()
        for k, v in query_params.items():
            if v == '':
                del query_params[k]
        request.GET = query_params
        return super(CustomerViewSet, self).initialize_request(request, *args, **kwargs)

