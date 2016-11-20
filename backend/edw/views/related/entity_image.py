# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
from rest_framework import permissions

from rest_framework_filters.backends import DjangoFilterBackend

from edw.models.related import EntityImageModel
from edw.rest.viewsets import remove_empty_params_from_request
from edw.rest.filters.related.entity_image import EntityImageFilter
from edw.rest.serializers.related.entity_image import EntityImageSerializer


class EntityImageViewSet(viewsets.ModelViewSet):

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,) # IsOwnerOrReadOnly

    queryset = EntityImageModel.objects.all()
    serializer_class = EntityImageSerializer
    filter_class = EntityImageFilter
    filter_backends = (DjangoFilterBackend,)

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(EntityImageViewSet, self).initialize_request(*args, **kwargs)

    def list(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None:
            request.GET.setdefault('entity', entity_pk)
        return super(EntityImageViewSet, self).list(request, *args, **kwargs)

    def create(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None and request.data.get('entity', None) is None:
            request.data['entity'] = entity_pk
        return super(EntityImageViewSet, self).create(request, *args, **kwargs)

    def update(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None and request.data.get('entity', None) is None:
            request.data['entity'] = entity_pk
        return super(EntityImageViewSet, self).update(request, *args, **kwargs)
