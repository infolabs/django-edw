# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
from rest_framework import permissions

from rest_framework_filters.backends import DjangoFilterBackend

from edw.models.related.entity_file import EntityFileModel
from edw.rest.viewsets import remove_empty_params_from_request
from edw.rest.filters.related.entity_file import EntityFileFilter
from edw.rest.serializers.related.entity_file import EntityFileSerializer
from edw.rest.permissions import IsFilerFileOwnerOrReadOnly


class EntityFileViewSet(viewsets.ModelViewSet):

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsFilerFileOwnerOrReadOnly)

    queryset = EntityFileModel.objects.all()
    serializer_class = EntityFileSerializer
    filter_class = EntityFileFilter
    filter_backends = (DjangoFilterBackend,)

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(EntityFileViewSet, self).initialize_request(*args, **kwargs)

    def list(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None:
            request.GET.setdefault('entity', entity_pk)
        return super(EntityFileViewSet, self).list(request, *args, **kwargs)

    def create(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None and request.data.get('entity', None) is None:
            request.data['entity'] = entity_pk
        return super(EntityFileViewSet, self).create(request, *args, **kwargs)

    def update(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None and request.data.get('entity', None) is None:
            request.data['entity'] = entity_pk
        return super(EntityFileViewSet, self).update(request, *args, **kwargs)
