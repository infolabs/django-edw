# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import serializers

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.data_mart import (
    DataMartCommonSerializer,
    DataMartSummarySerializer,
    DataMartDetailSerializer,
    DataMartTreeSerializer,
)

from edw.rest.filters.data_mart import DataMartFilter
from edw.models.data_mart import DataMartModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request
from edw.rest.pagination import DataMartPagination


class DataMartViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving data marts.
    Additional actions:
        `tree` - retrieve tree action. `GET /edw/api/data-marts/tree/`
    """
    queryset = DataMartModel.objects.all()
    serializer_class = DataMartCommonSerializer
    custom_serializer_classes = {
        'list':  DataMartSummarySerializer,
        'retrieve':  DataMartDetailSerializer,
    }

    filter_class = DataMartFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    pagination_class = DataMartPagination

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(DataMartViewSet, self).initialize_request(*args, **kwargs)

    @list_route(filter_backends=())
    def tree(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None:
            request.GET.setdefault('parent_id', data_mart_pk)
        parent_id = request.query_params.get('parent_id', None)
        if parent_id is not None:
            parent = get_object_or_404(DataMartModel.objects.all(),
                                       pk=serializers.IntegerField().to_internal_value(parent_id))
            queryset = parent.get_children()
        else:
            queryset = DataMartModel.objects.toplevel()
        serializer = DataMartTreeSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def list(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None:
            request.GET.setdefault('parent_id', data_mart_pk)
        return super(DataMartViewSet, self).list(request, *args, **kwargs)