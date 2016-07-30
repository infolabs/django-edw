# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, filters
from rest_framework.decorators import list_route#, detail_route
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
from edw.rest.viewsets import CustomSerializerViewSetMixin




class TermViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving terms.
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

    def initialize_request(self, request, *args, **kwargs):
        """
        Remove empty query params from request
        """
        query_params = request.GET.copy()
        for k, v in query_params.items():
            if v == '':
                del query_params[k]
        request.GET = query_params
        return super(TermViewSet, self).initialize_request(request, *args, **kwargs)

    @list_route()
    def tree(self, request, format=None):
        #print "******** TEST ********"
        #print "**********************"

        #print TermModel.decompress([4, 5], fix_it=False)

        #print "**********************"
        #print "**********************"

        queryset = TermModel.objects.toplevel()
        serializer = TermTreeSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)



