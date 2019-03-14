# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.core import urlresolvers

from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from rest_framework_filters.backends import DjangoFilterBackend

from rest_framework_bulk.generics import BulkModelViewSet

from edw.rest.serializers.term import (
    TermSerializer,
    TermSummarySerializer,
    TermDetailSerializer,
    TermTreeSerializer,
)
from edw.rest.filters.term import TermFilter
from edw.models.term import TermModel
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request
from edw.rest.pagination import TermPagination
from edw.rest.permissions import IsSuperuserOrReadOnly



# class TermViewSet(CustomSerializerViewSetMixin, viewsets.ModelViewSet):
class TermViewSet(CustomSerializerViewSetMixin, BulkModelViewSet):
    """
    A simple ViewSet for listing or retrieving terms.
    Additional actions:
        `tree` - retrieve tree action. `GET /edw/api/terms/tree/`
    """
    queryset = TermModel.objects.all()
    serializer_class = TermSerializer
    custom_serializer_classes = {
        'list':  TermSummarySerializer,
        'retrieve':  TermDetailSerializer,

        'create': TermDetailSerializer,
        'update': TermDetailSerializer,
        'partial_update': TermDetailSerializer,
        'partial_bulk_update': TermDetailSerializer,
        'bulk_destroy': TermSerializer
    }

    permission_classes = [IsSuperuserOrReadOnly]

    filter_class = TermFilter
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter,)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    pagination_class = TermPagination

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(TermViewSet, self).initialize_request(*args, **kwargs)

    @list_route(filter_backends=())
    def tree(self, request, data_mart_pk=None, term_pk=None, format=None):
        '''
        Retrieve tree action
        :param request:
        :param data_mart_pk:
        :param format:
        :return:
        '''
        context = {
            "request": request
        }

        data_mart_pk = request.GET.get('data_mart_pk', data_mart_pk)
        if data_mart_pk is not None:
            context["data_mart_pk"] = data_mart_pk


        if term_pk is not None:
            request.GET.setdefault('parent_id', term_pk)
        parent_id = request.query_params.get('parent_id', None)

        if parent_id is not None:
            parent_id = serializers.IntegerField().to_internal_value(parent_id)
            parent = get_object_or_404(TermModel.objects.all(), pk=parent_id)
            context['root_pk'] = parent_id
            queryset = parent.get_children()
        else:
            queryset = TermModel.objects.toplevel()

        serializer = TermTreeSerializer(queryset, many=True, context=context)
        return Response(serializer.data)

    def list(self, request, data_mart_pk=None, term_pk=None, *args, **kwargs):
        if term_pk is not None:
            request.GET.setdefault('parent_id', term_pk)
        if data_mart_pk is not None:
            request.GET.setdefault('data_mart_pk', data_mart_pk)
        return super(TermViewSet, self).list(request, *args, **kwargs)


class RebuildTermTreeView(APIView):
    """
    Rebuilds MPTT tree
    """
    permission_classes = (IsAdminUser,)

    def get(self, request):
        TermModel._tree_manager.rebuild2()
        app_label = TermModel._meta.app_label

        messages.add_message(request._request, messages.INFO,
                             _("The tree was sucessfully rebuilt"))
        return HttpResponseRedirect(urlresolvers.reverse(
            "admin:%s_term_changelist" % app_label)
        )


