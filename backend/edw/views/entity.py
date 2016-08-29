# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
#from rest_framework.decorators import list_route
#from rest_framework.response import Response
from rest_framework import pagination


from edw.rest.serializers.entity import (
    EntitySerializer,
    EntityListSerializer,
    EntityDetailSerializer
)

from edw.rest.filters.entity import EntityFilter
from edw.models.entity import EntityModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request


class EntityViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving entities.
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

    """
    @list_route(filter_backends=())
    def detailed(self, request, data_mart_pk=None, format=None):
        '''
        Retrieve tree action
        :param request:
        :param data_mart_pk:
        :param format:
        :return:
        '''
        context = {
            "request": request
        }
        if data_mart_pk is not None:
            context["data_mart_pk"] = data_mart_pk

        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = EntityListSerializer(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)

        serializer = EntityListSerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    """
