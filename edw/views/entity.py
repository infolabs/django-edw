# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
#from rest_framework.decorators import list_route, detail_route
#from rest_framework.response import Response


from edw.rest.serializers.entity import (
    EntitySerializer,
    EntityListSerializer,
    EntityDetailSerializer
)

from edw.rest.filters.entity import EntityFilter
from edw.models.entity import EntityModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request


class EntityViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving entities.
    """
    queryset = EntityModel.objects.all()
    serializer_class = EntitySerializer
    custom_serializer_classes = {
        'list':  EntityListSerializer,
        'retrieve':  EntityDetailSerializer,
    }

    filter_class = EntityFilter

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(EntityViewSet, self).initialize_request(*args, **kwargs)
