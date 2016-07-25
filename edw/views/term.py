# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import generics
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from edw.rest.serializers.term import TermSelectSerializer
from edw.models.term import TermModel


class TermSelectView(generics.ListAPIView):
    """
    A simple list view, which is used only by the admin backend. It is required to fetch
    the data for rendering the select widget when looking up for a product.
    """
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    serializer_class = TermSelectSerializer

    def get_queryset(self):

        #return TermModel.objects.all()[:10]
        return TermModel.objects.active().toplevel()

        '''
        term = self.request.GET.get('term', '')
        if len(term) >= 2:
            return ProductModel.objects.select_lookup(term)[:10]
        return ProductModel.objects.all()[:10]
        '''