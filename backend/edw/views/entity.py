# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import pagination


from edw.rest.serializers.entity import (
    EntitySerializer,
    EntityListSerializer,
    EntityDetailSerializer
)

from edw.models.entity import EntityModel
from edw.rest.filters.entity import EntityFilter
from edw.rest.serializers.data_mart import DataMartDetailSerializer
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request


class EntityViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving entities.
    Additional actions:
        `data_mart` - retrieve data mart for entity. `GET /edw/api/entities/<id>/data_mart/`
    """
    queryset = EntityModel.objects.all()
    serializer_class = EntitySerializer
    custom_serializer_classes = {
        'list':  EntityListSerializer,
        'retrieve':  EntityDetailSerializer,
    }

    filter_class = EntityFilter

    pagination_class = pagination.LimitOffsetPagination

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(EntityViewSet, self).initialize_request(*args, **kwargs)

    @detail_route(filter_backends=())
    def data_mart(self, request, format=None, **kwargs):
        '''
        Retrieve entity data mart
        :param request:
        :param format:
        :return:
        '''
        instance = self.get_object()
        data_mart = instance.data_mart

        if data_mart is not None:
            context = {
                "request": request
            }
            serializer = DataMartDetailSerializer(data_mart, context=context)
            return Response(serializer.data)
        else:
            return Response({})
