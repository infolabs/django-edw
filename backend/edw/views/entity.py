# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

from rest_framework import viewsets, filters, pagination
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.entity import (
    EntityCommonSerializer,
    # EntitySummarySerializer,
    EntityTotalSummarySerializer,
    EntityDetailSerializer
)

from edw.models.entity import EntityModel
from edw.rest.filters.entity import EntityFilter
from edw.rest.serializers.data_mart import DataMartDetailSerializer
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request


class EntityViewSet(CustomSerializerViewSetMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving entities.
    Additional actions:
        `data_mart` - retrieve data mart for entity. `GET /edw/api/entities/<id>/data-mart/`
    """
    queryset = EntityModel.objects.all()
    serializer_class = EntityCommonSerializer
    custom_serializer_classes = {
        # 'list':  EntitySummarySerializer,
        'list':  EntityTotalSummarySerializer,
        'retrieve':  EntityDetailSerializer,
    }

    template_name = None
    data_mart_pk = None
    format = None

    renderer_classes = (JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer)

    filter_class = EntityFilter
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter)
    ordering_fields = ('created_at',)

    pagination_class = pagination.LimitOffsetPagination

    @remove_empty_params_from_request
    def initialize_request(self, *args, **kwargs):
        return super(EntityViewSet, self).initialize_request(*args, **kwargs)

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




    def list(self, request, data_mart_pk=None, *args, **kwargs):

        if self.data_mart_pk is not None:
           data_mart_pk = self.data_mart_pk
        if data_mart_pk is not None:
            request.GET['data_mart_pk'] = data_mart_pk
        return super(EntityViewSet, self).list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(EntityViewSet, self).get_serializer_context()
        context.update(self.queryset_context)
        return context

    def filter_queryset(self, queryset):
        queryset = super(EntityViewSet, self).filter_queryset(queryset)
        self.queryset_context = {
            "initial_filter_meta": self.request.GET['_initial_filter_meta'],
            "initial_queryset": self.request.GET['_initial_queryset'],
            "terms_filter_meta": self.request.GET['_terms_filter_meta'],
            "filter_queryset": queryset
        }
        return queryset


class EntitySubjectViewSet(EntityViewSet):

    def dispatch(self, request, *args, **kwargs):
        subj = kwargs.get('entity_pk', None)
        if subj is not None:
            del kwargs['entity_pk']
            request.GET = request.GET.copy()
            request.GET.setdefault('subj', subj)
        return super(EntityViewSet, self).dispatch(request, *args, **kwargs)
