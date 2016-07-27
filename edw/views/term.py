# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

#from rest_framework import generics
from rest_framework import viewsets
#from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from edw.rest.serializers.term import TermSerializer
from edw.models.term import TermModel


class TermViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving terms.
    """
    def list(self, request, format=None):

        print "******** TEST ********"
        print "**********************"

        print TermModel.decompress([2, 5])

        print "**********************"
        print "**********************"

        queryset = TermModel.objects.toplevel() #.active()
        serializer = TermSerializer(queryset, many=True, context={"arg1": "var1"})
        return Response(serializer.data)

    def retrieve(self, request, pk=None, format=None):
        queryset = TermModel.objects.all()
        term = get_object_or_404(queryset, pk=pk)
        serializer = TermSerializer(term)
        return Response(serializer.data)

'''
class TermSelectView(generics.ListAPIView):
    """
    A simple list view, which is used only by the admin backend. It is required to fetch
    the data for rendering the select widget when looking up for a product.
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = TermSerializer

    def get_queryset(self):

        return TermModel.objects.active().toplevel()

        """
        term = self.request.GET.get('term', '')
        if len(term) >= 2:
            return ProductModel.objects.select_lookup(term)[:10]
        return ProductModel.objects.all()[:10]
        """
'''