# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.core import urlresolvers

from rest_framework import filters
from rest_framework.response import Response
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
from edw.views.generics import get_object_or_404

try:
    # rest_framework 3.3.3
    from rest_framework.decorators import list_route
except ImportError:
    # rest_framework 3.10.3
    from rest_framework.decorators import action

    def list_route(methods=None, **kwargs):
        return action(detail=False, **kwargs)


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
        'bulk_update': DataMartDetailSerializer,
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

    def get_object(self):
        # try find object by `slug`
        # save origin lookups for monkey path
        origin_lookup_url_kwarg, origin_lookup_field = self.lookup_url_kwarg, self.lookup_field

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        # it was a string, not an int.
        try:
            int(self.kwargs[lookup_url_kwarg])
        except ValueError:
            self.lookup_url_kwarg, self.lookup_field = 'pk', 'slug'

        obj = super(DataMartViewSet, self).get_object()

        self.lookup_url_kwarg, self.lookup_field = origin_lookup_url_kwarg, origin_lookup_field
        return obj

    @list_route(filter_backends=())
    def tree(self, request, data_mart_pk=None, *args, **kwargs):
        if data_mart_pk is not None:
            request.GET.setdefault('parent_id', data_mart_pk)
        value = request.query_params.get('parent_id', None)
        if value is not None:
            # try find object by `slug`
            try:
                value = int(value)
            except ValueError:
                # it was a string, not an int.
                if value.lower() in ('none', 'null'):
                    queryset = DataMartModel.objects.toplevel()
                else:
                    queryset = get_object_or_404(DataMartModel.objects.all(), slug=value).get_children()
            else:
                queryset = get_object_or_404(DataMartModel.objects.all(), pk=value).get_children()
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
