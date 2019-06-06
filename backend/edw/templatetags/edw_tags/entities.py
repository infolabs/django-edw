# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from classytags.core import Options
from classytags.arguments import MultiKeywordArgument, Argument
from rest_framework_filters.backends import DjangoFilterBackend

from edw.models.entity import EntityModel
from edw.rest.templatetags import BaseRetrieveDataTag
from edw.rest.serializers.entity import (
    EntityTotalSummarySerializer,
    EntityDetailSerializer,
)
from edw.rest.filters.entity import (
    EntityFilter,
    EntityMetaFilter,
    EntityDynamicFilter,
    EntityGroupByFilter,
    EntityOrderingFilter
)
from edw.rest.pagination import EntityPagination


class GetEntity(BaseRetrieveDataTag):
    name = 'get_entity'
    queryset = EntityModel.objects.all()
    serializer_class = EntityDetailSerializer
    action = 'retrieve'

    options = Options(
        Argument('pk', resolve=True),
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, pk, kwargs, varname):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if varname:
            context[varname] = data
            return ''
        else:
            return self.to_json(data)


class GetEntities(BaseRetrieveDataTag):
    name = 'get_entities'
    queryset = EntityModel.objects.all()
    serializer_class = EntityTotalSummarySerializer
    action = 'list'

    filter_class = EntityFilter
    filter_backends = (DjangoFilterBackend, EntityDynamicFilter, EntityMetaFilter, EntityGroupByFilter,
                       EntityOrderingFilter)
    ordering_fields = '__all__'

    pagination_class = EntityPagination

    options = Options(
        MultiKeywordArgument('kwargs', required=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, kwargs, varname):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = self.get_paginated_data(serializer.data)
            pagination = {
                "limit": self.paginator.limit,
                "offset": self.paginator.offset,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
            }
            data.update(pagination)
            context["{}_paginator".format(varname)] = self.paginator
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

        if varname:
            context[varname] = data
            return ''
        else:
            return self.to_json(data)

    def get_serializer_context(self):
        context = super(GetEntities, self).get_serializer_context()
        context.update(self.queryset_context)
        return context

    def filter_queryset(self, queryset):
        queryset = super(GetEntities, self).filter_queryset(queryset)
        query_params = self.request.GET

        data_mart = query_params['_data_mart']
        if data_mart is not None:
            query_params.setdefault(self.paginator.limit_query_param, str(data_mart.limit))

        self.queryset_context = {
            "data_mart": data_mart,
            "extra": None
        }
        self.queryset_context.update({key: query_params['_{}'.format(key)] for key in (
            "initial_filter_meta", "initial_queryset", "terms_filter_meta", "terms_ids", "subj_ids", "ordering",
            "view_component", "annotation_meta", "aggregation_meta", "group_by", "alike", "filter_queryset")})

        return queryset
