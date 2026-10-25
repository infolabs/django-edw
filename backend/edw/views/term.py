# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse

from rest_framework import filters
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

from rest_framework_bulk.generics import BulkModelViewSet

from edw.rest.serializers.term import (
    TermSerializer,
    TermSummarySerializer,
    TermDetailSerializer,
    TermTreeSerializer,
)
from edw.rest.filters.term import TermFilter
from edw.rest.filters.backends import EDWFilterBackend
from edw.models.data_mart import DataMartModel
from edw.models.term import TermModel
from edw.rest.viewsets import (
    BulkDestroyPolicyMixin,
    CustomSerializerViewSetMixin,
    SingleWriteAliasGuardMixin,
    enforce_url_scope,
    remove_empty_params_from_request,
)
from edw.rest.pagination import TermPagination
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


class TermViewSet(BulkDestroyPolicyMixin, SingleWriteAliasGuardMixin,
                 CustomSerializerViewSetMixin, BulkModelViewSet):
    """
    A simple ViewSet for listing or retrieving terms.
    Additional actions:
        `tree` - retrieve tree action. `GET /edw/api/terms/tree/`
    """
    queryset = TermModel.objects.all()
    serializer_class = TermSerializer
    custom_serializer_classes = {
        'list': TermSummarySerializer,
        'retrieve': TermDetailSerializer,
        'create': TermDetailSerializer,
        'update': TermDetailSerializer,
        'bulk_update': TermDetailSerializer,
        'partial_update': TermDetailSerializer,
        'partial_bulk_update': TermDetailSerializer,
        'bulk_destroy': TermSerializer
    }

    permission_classes = [IsSuperuserOrReadOnly]

    filterset_class = TermFilter
    filter_backends = (filters.SearchFilter, EDWFilterBackend, filters.OrderingFilter,)
    search_fields = ('name', 'slug')
    ordering_fields = ('name', )

    pagination_class = TermPagination

    bulk_destroy_scope_params = ('id__in', 'slug', 'path', 'parent_id', 'data_mart_pk')
    # E9/R1: only a parameter the TermFilter really declares and applies may
    # bound a collection DELETE.
    bulk_destroy_requires_declared_filters = True

    # E9/R2: nested URL scope captured in ``initial`` (see ``initial``).
    bulk_scope_parent_raw = None
    bulk_scope_data_mart_raw = None
    _bulk_scope_parent_pk = None
    _bulk_scope_parent_pk_resolved = False

    def allow_bulk_destroy(self, qs, filtered):
        """
        Collection DELETE is refused unless the request names a concrete,
        filterset-declared scope, every named term is a leaf without a delete
        restriction, and the complete deletion effect set is exactly the named
        terms (no implicit MPTT/CASCADE cascade).
        """
        if not self._has_explicit_bulk_destroy_scope(filtered):
            return False
        if not self._bulk_destroy_targets_are_explicit(filtered):
            return False
        return self._bulk_destroy_effect_is_explicit(filtered)

    def _named_delete_data_mart_pks(self):
        """
        Data-mart ids explicitly named by this DELETE (nested URL or query).

        They are the only foreign side whose M2M membership row may be removed
        implicitly by a term delete; a data mart that the request does not name
        is a foreign consequence and stays default-deny.
        """
        query = self._bulk_destroy_query_data() or {}
        value = query.get('data_mart_pk')
        if value in (None, ''):
            value = getattr(self, 'bulk_scope_data_mart_raw', None)
        if value in (None, ''):
            return set()
        try:
            return {int(value)}
        except (TypeError, ValueError):
            pk = DataMartModel.materialized._default_manager.filter(
                slug=value).values_list('pk', flat=True).first()
            return {pk} if pk is not None else set()

    def _delete_effect_is_allowed(self, obj):
        """
        E11/R4: an auto-created data-mart membership row is authorized only
        when the request names that exact data mart.
        """
        pks = self._named_delete_data_mart_pks()
        if not pks:
            return False
        through = DataMartModel.materialized.terms.through
        if not isinstance(obj, through):
            return False
        return getattr(obj, 'datamart_id', None) in pks

    @remove_empty_params_from_request()
    def initialize_request(self, *args, **kwargs):
        return super(TermViewSet, self).initialize_request(*args, **kwargs)

    def initial(self, request, *args, **kwargs):
        # E9/R2: nested /terms/<term_pk>/children/ and
        # /data-marts/<data_mart_pk>/terms/ scope every action, not only list.
        # The URL value is mandatory: a different query value is refused and
        # the request body cannot replace it (see the serializers).
        term_pk = kwargs.get('term_pk')
        if term_pk is not None:
            enforce_url_scope(request, 'parent_id', term_pk, _('term'))
            self.bulk_scope_parent_raw = str(term_pk)
        data_mart_pk = kwargs.get('data_mart_pk')
        if data_mart_pk is not None:
            enforce_url_scope(request, 'data_mart_pk', data_mart_pk, _('data mart'))
            self.bulk_scope_data_mart_raw = str(data_mart_pk)
        return super(TermViewSet, self).initial(request, *args, **kwargs)

    def get_bulk_scope_parent_pk(self):
        """Resolved pk of the mandatory nested URL parent (None if absent)."""
        raw = self.bulk_scope_parent_raw
        if raw is None:
            return None
        if not self._bulk_scope_parent_pk_resolved:
            self._bulk_scope_parent_pk_resolved = True
            try:
                self._bulk_scope_parent_pk = int(raw)
            except (TypeError, ValueError):
                self._bulk_scope_parent_pk = TermModel.objects.filter(
                    slug=raw).values_list('pk', flat=True).first()
        return self._bulk_scope_parent_pk

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

        obj = super(TermViewSet, self).get_object()

        self.lookup_url_kwarg, self.lookup_field = origin_lookup_url_kwarg, origin_lookup_field
        return obj

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
        value = request.query_params.get('parent_id', None)

        if value is not None:
            # try find object by `slug`
            try:
                value = int(value)
            except ValueError:
                # it was a string, not an int.
                if value.lower() in ('none', 'null'):
                    queryset = TermModel.objects.toplevel()
                else:
                    parent = get_object_or_404(TermModel.objects.all(), slug=value)
                    context['root_pk'] = parent.id
                    queryset = parent.get_children()
            else:
                parent = get_object_or_404(TermModel.objects.all(), pk=value)
                context['root_pk'] = value
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
        return HttpResponseRedirect(reverse(
            "admin:%s_term_changelist" % app_label)
        )


