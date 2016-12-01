# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer, TemplateHTMLRenderer

from rest_framework_filters.backends import DjangoFilterBackend

from edw.rest.serializers.entity import (
    EntityCommonSerializer,
    EntityTotalSummarySerializer,
    EntityDetailSerializer
)

from edw.models.entity import EntityModel
from edw.rest.filters.entity import EntityFilter, EntityMetaFilter, EntityOrderingFilter
from edw.rest.serializers.data_mart import DataMartDetailSerializer
from edw.rest.viewsets import CustomSerializerViewSetMixin, remove_empty_params_from_request
from edw.rest.pagination import EntityPagination


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
    filter_backends = (DjangoFilterBackend, EntityMetaFilter, EntityOrderingFilter)
    # ordering_fields = ('created_at',)
    ordering_fields = '__all__'

    pagination_class = EntityPagination

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
            request.GET.setdefault('data_mart_pk', data_mart_pk)
        return super(EntityViewSet, self).list(request, *args, **kwargs)

    def get_serializer_context(self):
        context = super(EntityViewSet, self).get_serializer_context()
        context.update(self.queryset_context)
        return context

    def filter_queryset(self, queryset):
        queryset = super(EntityViewSet, self).filter_queryset(queryset)
        query_params = self.request.GET
        self.queryset_context = {
            "initial_filter_meta": query_params['_initial_filter_meta'],
            "initial_queryset": query_params['_initial_queryset'],
            "terms_filter_meta": query_params['_terms_filter_meta'],
            "data_mart": query_params['_data_mart'],
            "subj_ids": query_params['_subj_ids'],
            "ordering": query_params['_ordering'],
            "view_component": query_params['_view_component'],
            "filter_queryset": queryset
        }
        return queryset

    # #
    # # TEST
    # #
    #
    # def retrieve(self, request, *args, **kwargs):
    #
    #     from rest_framework.generics import get_object_or_404
    #
    #     from edw.models.term import TermModel
    #
    #     from nash_region.models.person.responsible_person import ResponsiblePerson
    #
    #     pk = kwargs.get('pk')
    #
    #     qs = EntityModel.objects.all()
    #     obj = get_object_or_404(qs, pk=pk)
    #
    #     print "Base object:", obj.id, obj
    #
    #     # queryset = EntityModel.objects.all()
    #     # queryset = EntityModel.objects.exclude(pk=pk)
    #     queryset = EntityModel.objects.instance_of(ResponsiblePerson).active()
    #
    #     # entity_terms_ids = obj.terms.active().values_list('id', flat=True)
    #     entity_terms_ids = obj.terms.active().exclude(
    #         system_flags=TermModel.system_flags.external_tagging_restriction).values_list('id', flat=True)
    #
    #     same = queryset.get_similar(entity_terms_ids)
    #
    #     print "Similar object:", same.id, same
    #
    #     return super(EntityViewSet, self).retrieve(request, *args, **kwargs)
    #
    # #
    # #


class EntitySubjectViewSet(EntityViewSet):

    def dispatch(self, request, *args, **kwargs):
        subj = kwargs.get('entity_pk', None)
        if subj is not None:
            del kwargs['entity_pk']
            request.GET = request.GET.copy()
            request.GET.setdefault('subj', subj)
        return super(EntityViewSet, self).dispatch(request, *args, **kwargs)
