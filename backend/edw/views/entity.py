# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.apps import apps

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer
from rest_framework.generics import get_object_or_404

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.entity import (
    EntityCommonSerializer,
    EntityTotalSummarySerializer,
    EntityDetailSerializer
)

from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.rest.filters.entity import (
    EntityFilter,
    EntityMetaFilter,
    EntityDynamicFilter,
    EntityGroupByFilter,
    EntityOrderingFilter
)
from edw.rest.serializers.data_mart import DataMartDetailSerializer
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request
from edw.rest.pagination import EntityPagination
from edw.rest.permissions import IsReadOnly


class EntityViewSet(CustomSerializerViewSetMixin, viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving entities.
    Additional actions:
        `data_mart` - retrieve data mart for entity. `GET /edw/api/entities/<id>/data-mart/`
    """
    queryset = EntityModel.objects.all()
    serializer_class = EntityCommonSerializer
    # serializer_class = EntityCommonSerializer
    custom_serializer_classes = {
        # 'list':  EntitySummarySerializer,
        'list':  EntityTotalSummarySerializer,
        'retrieve':  EntityDetailSerializer,
        'create': EntityDetailSerializer,
        'update': EntityDetailSerializer,
        'partial_update': EntityDetailSerializer
    }

    # serializer_context = None
    extra_serializer_context = None
    template_name = None
    terms = None
    data_mart_pk = None
    subj = None
    format = None

    permission_classes = [IsReadOnly]

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer)

    filter_class = EntityFilter
    filter_backends = (DjangoFilterBackend, EntityDynamicFilter, EntityMetaFilter, EntityGroupByFilter,
                       EntityOrderingFilter)
    ordering_fields = '__all__'

    pagination_class = EntityPagination

    REQUEST_CACHED_SERIALIZED_DATA_KEY = '_cached_serialized_data'

    @remove_empty_params_from_request(exclude=('active',))
    def initialize_request(self, *args, **kwargs):
        return super(EntityViewSet, self).initialize_request(*args, **kwargs)

    def initial(self, request, data_mart_pk=None, *args, **kwargs):
        super(EntityViewSet, self).initial(request, *args, **kwargs)
        if hasattr(self.extra_serializer_context, '__call__'):
            self.extra_serializer_context = self.extra_serializer_context(self, request, *args, **kwargs)
        if self.data_mart_pk is not None:
            request.GET['data_mart_pk'] = str(self.data_mart_pk)
        elif data_mart_pk is not None:
            request.GET.setdefault('data_mart_pk', data_mart_pk)

    @detail_route(filter_backends=(), url_path='data-mart')
    def data_mart(self, request, format=None, **kwargs):
        '''
        Retrieve entity data mart
        :param request:
        :param format:
        :return:
        '''
        instance = self.get_object()
        data_mart = instance.data_mart

        if data_mart is not None:
            context = {
                "request": request
            }
            serializer = DataMartDetailSerializer(data_mart, context=context)
            return Response(serializer.data)
        else:
            return Response({})

    def get_format_suffix(self, **kwargs):
        """
        Determine if the request includes a '.json' style format suffix
        """
        if self.format is not None:
            kwargs[self.settings.FORMAT_SUFFIX_KWARG] = self.format
        return super(EntityViewSet, self).get_format_suffix(**kwargs)

    def list(self, request, *args, **kwargs):
        request.GET.setdefault('active', True)
        if self.terms is not None:
            request.GET['terms'] = ','.join([str(x) for x in self.terms]) if isinstance(
                self.terms, (list, tuple)) else str(self.terms)
        if self.subj is not None:
            request.GET['subj'] = ','.join([str(x) for x in self.subj]) if isinstance(
                self.subj, (list, tuple)) else str(self.subj)
        return super(EntityViewSet, self).list(request, *args, **kwargs)

    def get_object(self):
        obj = getattr(self, '_obj', None)
        if obj is None:
            obj = self._obj = super(EntityViewSet, self).get_object()
        return obj

    def check_permissions(self, request):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        try:
            request.GET['_mutable'] = True
        except AttributeError:
            request.GET = request.GET.copy()
        request.GET['_data_mart'] = None

        model_class = EntityModel
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy'):
            obj = self.get_object()
            model_class = obj.__class__
        elif self.action in ('create', 'list'):
            data_mart_pk = self.kwargs.get('data_mart_pk', None)
            if data_mart_pk is not None:
                request.GET['_data_mart'] = data_mart = get_object_or_404(DataMartModel.objects.active(),
                                                                          pk=data_mart_pk)
                model_class = data_mart.entities_model
            else:
                entity_model = request.data.get('entity_model', None)
                if entity_model is not None:
                    try:
                        model_class = apps.get_model(EntityModel._meta.app_label, str(entity_model))
                    except LookupError:
                        pass

        permissions = [permission() for permission in model_class._rest_meta.permission_classes]

        if not permissions:
            permissions = self.get_permissions()

        for permission in permissions:
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def check_object_permissions(self, request, obj):
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        permissions = [permission() for permission in obj._rest_meta.permission_classes]
        if not permissions:
            permissions = self.get_permissions()

        for permission in permissions:
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def get_serializer_context(self):
        context = super(EntityViewSet, self).get_serializer_context()

        if hasattr(self, 'serializer_context'):
             context.update(self.serializer_context)

        if self.extra_serializer_context is not None:
            context.update(self.extra_serializer_context)
        return context

    def filter_queryset(self, queryset):
        queryset = super(EntityViewSet, self).filter_queryset(queryset)
        query_params = self.request.GET

        data_mart = query_params['_data_mart']
        if data_mart is not None:
            query_params.setdefault(self.paginator.limit_query_param, str(data_mart.limit))

        self.serializer_context = {
            "initial_filter_meta": query_params['_initial_filter_meta'],
            "initial_queryset": query_params['_initial_queryset'],
            "terms_filter_meta": query_params['_terms_filter_meta'],
            "data_mart": data_mart,
            "terms_ids": query_params['_terms_ids'],
            "subj_ids": query_params['_subj_ids'],
            "ordering": query_params['_ordering'],
            "view_component": query_params['_view_component'],
            "annotation_meta": query_params['_annotation_meta'],
            "aggregation_meta": query_params['_aggregation_meta'],
            "group_by": query_params['_group_by'],
            "alike": query_params['_alike'],
            "filter_queryset": query_params['_filter_queryset']
        }
        return queryset

    def finalize_response(self, request, response, *args, **kwargs):
        request.GET[self.REQUEST_CACHED_SERIALIZED_DATA_KEY] = response.data
        return super(EntityViewSet, self).finalize_response(request, response, *args, **kwargs)


class EntitySubjectViewSet(EntityViewSet):

    def dispatch(self, request, *args, **kwargs):
        subj = kwargs.get('entity_pk', None)
        if subj is not None:
            del kwargs['entity_pk']
            request.GET = request.GET.copy()
            request.GET.setdefault('subj', subj)
        return super(EntityViewSet, self).dispatch(request, *args, **kwargs)
