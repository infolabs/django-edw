# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.term import (
    TermSerializer,
    TermListSerializer,
    TermDetailSerializer,
    TermTreeSerializer,
)
from edw.rest.filters.term import TermFilter
from edw.models.term import TermModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request


class TermViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving terms.
    Additional actions:
        `tree` - retrieve tree action. `GET /edw/api/terms/tree/`
    """
    queryset = TermModel.objects.all()
    serializer_class = TermSerializer
    custom_serializer_classes = {
        'list':  TermListSerializer,
        'retrieve':  TermDetailSerializer,
    }

    filter_class = TermFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter,)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(TermViewSet, self).initialize_request(*args, **kwargs)

    @list_route(filter_backends=())
    def tree(self, request, data_mart_pk=None, format=None):
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

        queryset = TermModel.objects.toplevel()
        serializer = TermTreeSerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    @detail_route()
    def children(self, request, pk, format=None, **kwargs):
        '''
        Retrieve children nodes, just adding `parent_id` filter
        :param request:
        :param pk:
        :param format:
        :return:
        '''
        request.GET['parent_id'] = pk
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        context = {
            "request": request
        }
        serializer_class = self.custom_serializer_classes['list']
        if page is not None:
            serializer = serializer_class(page, context=context, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(queryset, context=context, many=True)
        return Response(serializer.data)
