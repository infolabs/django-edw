# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from rest_framework import viewsets
from rest_framework import permissions

from edw.models.related.entity_image import EntityImageModel
from edw.rest.viewsets import remove_empty_params_from_request

from edw.rest.filters.backends import EDWFilterBackend
from edw.rest.filters.related.entity_image import EntityImageFilter as DefaultEntityImageFilter
from edw.rest.serializers.related.entity_image import EntityImageSerializer
from edw.rest.permissions import IsFilerFileOwnerOrReadOnly


#TODO: попробовать переделать по аналогии с Entity
entity_image_filter_class = getattr(settings, 'ENTITY_IMAGE_FILTER_CLASS', None)
if entity_image_filter_class:
    from django.utils.module_loading import import_string
    EntityImageFilter = import_string(entity_image_filter_class)
else:
    EntityImageFilter = DefaultEntityImageFilter


class EntityImageViewSet(viewsets.ModelViewSet):

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsFilerFileOwnerOrReadOnly)

    queryset = EntityImageModel.objects.all()
    serializer_class = EntityImageSerializer
    filter_class = EntityImageFilter
    filter_backends = (EDWFilterBackend,)

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(EntityImageViewSet, self).initialize_request(*args, **kwargs)

    def list(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None:
            request.GET.setdefault('entity', entity_pk)
        return super(EntityImageViewSet, self).list(request, *args, **kwargs)

    def create(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None and request.data.get('entity', None) is None:
            request.data['entity'] = entity_pk

        from edw.models.entity import EntityModel
        entity = EntityModel.objects.get(pk=request.data['entity'])
        if entity.entity_model == 'competitioninitiative':
            name = request.data['image'].name
            import hashlib
            import os
            salt = os.urandom(32)
            hash_name = hashlib.sha256(name.split('.')[0].encode('utf-8')+salt).hexdigest()
            request.data['image'].name = '{}.{}'.format(hash_name, name.split('.')[1])
        return super(EntityImageViewSet, self).create(request, *args, **kwargs)

    def update(self, request, entity_pk=None, *args, **kwargs):
        if entity_pk is not None and request.data.get('entity', None) is None:
            request.data['entity'] = entity_pk
        return super(EntityImageViewSet, self).update(request, *args, **kwargs)
