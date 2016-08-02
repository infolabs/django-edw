# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.response import Response

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.data_mart import (
    DataMartSerializer,
    DataMartListSerializer,
    DataMartDetailSerializer,
    DataMartTreeSerializer,
)

from edw.rest.filters.data_mart import DataMartFilter
from edw.models.data_mart import DataMartModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request


class DataMartViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving data marts.
    Additional actions:
        `tree` - retrieve tree action. `GET /edw/api/terms/tree/`
    """
    queryset = DataMartModel.objects.all()
    serializer_class = DataMartSerializer
    custom_serializer_classes = {
        'list':  DataMartListSerializer,
        'retrieve':  DataMartDetailSerializer,
    }

    filter_class = DataMartFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter,)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(DataMartViewSet, self).initialize_request(*args, **kwargs)

    @list_route(filter_backends=())
    def tree(self, request, format=None):
        queryset = DataMartModel.objects.toplevel()
        serializer = DataMartTreeSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

