# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.views.generic import DetailView

from rest_framework import viewsets
from rest_framework_filters.backends import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework import  permissions

from sample.models.book import Book

from edw.models.defaults.entity_image import EntityImage
from edw.rest.serializers.related.entity_image import EntityImageSerializer
from edw.rest.viewsets import remove_empty_params_from_request


class BookDetailView(DetailView):
    # context_object_name="event"
    template_name="sample/book_detail.html"

    def __init__(self, **kwargs):
        self.model = kwargs.get('model') or Book
        self.queryset = self.model.objects.all()
        super(BookDetailView, self).__init__(**kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        if self.object:
            context.update({
                'title': self.object.entity_name,
            })
        context.update(kwargs)
        return super(BookDetailView, self).get_context_data(**context)


class BookImageViewSet(viewsets.ModelViewSet):

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,) # IsOwnerOrReadOnly

    queryset = EntityImage.objects.all()
    serializer_class = EntityImageSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_backends = (OrderingFilter,)
    ordering_fields = '__all__'

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(BookImageViewSet, self).initialize_request(*args, **kwargs)