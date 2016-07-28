# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

#from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import list_route#, detail_route

#from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from edw.rest.serializers.term import TermSerializer, TermTreeSerializer
from edw.rest.filters.term import TermFilter
from edw.models.term import TermModel




class TermViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving terms.
    """
    queryset = TermModel.objects.all()
    serializer_class = TermSerializer
    filter_class = TermFilter

    @list_route()
    def tree(self, request, format=None):
        #print "******** TEST ********"
        #print "**********************"

        #print TermModel.decompress([4, 5], fix_it=False)

        #print "**********************"
        #print "**********************"

        queryset = TermModel.objects.toplevel().active()
        serializer = TermTreeSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

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


