# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.core import urlresolvers

from rest_framework import filters
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from rest_framework_filters.backends import DjangoFilterBackend

from rest_framework_bulk.generics import BulkModelViewSet

from edw.rest.serializers.data_mart import (
    DataMartCommonSerializer,
    DataMartSummarySerializer,
    DataMartDetailSerializer,
    DataMartTreeSerializer,
)

from edw.rest.filters.data_mart import DataMartFilter
from edw.models.data_mart import DataMartModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request
from edw.rest.pagination import DataMartPagination
from edw.rest.permissions import IsSuperuserOrReadOnly


class DataMartViewSet(CustomSerializerViewSetMixin, BulkModelViewSet):
    """
    A simple ViewSet for listing or retrieving data marts.
    Additional actions:
        `tree` - retrieve tree action. `GET /edw/api/data-marts/tree/`
    """
    queryset = DataMartModel.objects.all()
    serializer_class = DataMartCommonSerializer
    custom_serializer_classes = {
        'list': DataMartSummarySerializer,
        'retrieve': DataMartDetailSerializer,

        'create': DataMartDetailSerializer,
        'update': DataMartDetailSerializer,
        'partial_update': DataMartDetailSerializer,
        'partial_bulk_update': DataMartDetailSerializer,
        'bulk_destroy': DataMartCommonSerializer
    }

    permission_classes = [IsSuperuserOrReadOnly]

    filter_class = DataMartFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    pagination_class = DataMartPagination

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(DataMartViewSet, self).initialize_request(*args, **kwargs)

    @list_route(filter_backends=())
    def tree(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None:
            request.GET.setdefault('parent_id', data_mart_pk)
        parent_id = request.query_params.get('parent_id', None)
        if parent_id is not None:
            parent = get_object_or_404(DataMartModel.objects.all(),
                                       pk=serializers.IntegerField().to_internal_value(parent_id))
            queryset = parent.get_children()
        else:
            queryset = DataMartModel.objects.toplevel()
        serializer = DataMartTreeSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def list(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None:
            request.GET.setdefault('parent_id', data_mart_pk)
        return super(DataMartViewSet, self).list(request, *args, **kwargs)


class RebuildDataMartTreeView(APIView):
    """
    Rebuilds MPTT tree
    """
    permission_classes = (IsAdminUser,)

    def get(self, request):
        DataMartModel._tree_manager.rebuild2()
        app_label = DataMartModel._meta.app_label

        messages.add_message(request._request, messages.INFO,
                             _("The tree was sucessfully rebuilt"))
        return HttpResponseRedirect(urlresolvers.reverse(
            "admin:%s_term_changelist" % app_label)
        )
