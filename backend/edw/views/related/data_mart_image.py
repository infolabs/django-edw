# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
from rest_framework import permissions

from edw.models.related.data_mart_image import DataMartImageModel
from edw.rest.viewsets import remove_empty_params_from_request
from edw.rest.filters.related.data_mart_image import DataMartImageFilter
from edw.rest.filters.backends import EDWFilterBackend
from edw.rest.serializers.related.data_mart_image import DataMartImageSerializer
from edw.rest.permissions import IsFilerFileOwnerOrReadOnly


class DataMartImageViewSet(viewsets.ModelViewSet):

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsFilerFileOwnerOrReadOnly)

    queryset = DataMartImageModel.objects.all()
    serializer_class = DataMartImageSerializer
    filter_class = DataMartImageFilter
    filter_backends = (EDWFilterBackend,)

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(DataMartImageViewSet, self).initialize_request(*args, **kwargs)

    def list(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None:
            request.GET.setdefault('data_mart', data_mart_pk)
        return super(DataMartImageViewSet, self).list(request, *args, **kwargs)

    def create(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None and request.data.get('data_mart', None) is None:
            request.data['data_mart'] = data_mart_pk
        return super(DataMartImageViewSet, self).create(request, *args, **kwargs)

    def update(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None and request.data.get('data_mart', None) is None:
            request.data['data_mart'] = data_mart_pk
        return super(DataMartImageViewSet, self).update(request, *args, **kwargs)
