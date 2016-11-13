# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import serializers

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.term import (
    TermSerializer,
    TermSummarySerializer,
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
        'list':  TermSummarySerializer,
        'retrieve':  TermDetailSerializer,
    }

    filter_class = TermFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter,)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(TermViewSet, self).initialize_request(*args, **kwargs)

    # print "+++++++++++++++++++++++++++++"
    # print data_mart_pk, term_pk

    @list_route(filter_backends=())
    def tree(self, request, data_mart_pk=None, term_pk=None, format=None):
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

        data_mart_pk = request.GET.get('data_mart_pk', data_mart_pk)
        if data_mart_pk is not None:
            context["data_mart_pk"] = data_mart_pk


        if term_pk is not None:
            request.GET.setdefault('parent_id', term_pk)
        parent_id = request.query_params.get('parent_id', None)

        if parent_id is not None:
            parent = get_object_or_404(TermModel.objects.all(),
                                       pk=serializers.IntegerField().to_internal_value(parent_id))
            queryset = parent.get_children()
        else:
            queryset = TermModel.objects.toplevel()

        serializer = TermTreeSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    # @detail_route()
    # def children(self, request, pk, format=None, **kwargs):
    #     '''
    #     Retrieve children nodes, just adding `parent_id` filter
    #     :param request:
    #     :param pk:
    #     :param format:
    #     :return:
    #     '''
    #     request.GET['parent_id'] = pk
    #     queryset = self.filter_queryset(self.get_queryset())
    #     page = self.paginate_queryset(queryset)
    #     context = {
    #         "request": request
    #     }
    #     serializer_class = self.custom_serializer_classes['list']
    #     if page is not None:
    #         serializer = serializer_class(page, context=context, many=True)
    #         return self.get_paginated_response(serializer.data)
    #     serializer = serializer_class(queryset, context=context, many=True)
    #     return Response(serializer.data)

    def list(self, request, data_mart_pk=None, term_pk=None, *args, **kwargs):
        if term_pk is not None:
            request.GET.setdefault('parent_id', term_pk)
        if data_mart_pk is not None:
            request.GET.setdefault('data_mart_pk', data_mart_pk)
        return super(TermViewSet, self).list(request, *args, **kwargs)