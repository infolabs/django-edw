# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.mixins import ListModelMixin
from rest_framework.filters import SearchFilter

from drf_haystack.generics import HaystackGenericAPIView
from drf_haystack.viewsets import ViewSetMixin
from drf_haystack.filters import BaseHaystackFilterBackend
from drf_haystack.query import FilterQueryBuilder

import operator

from edw.models.entity import EntityModel
from edw.search.serializers import EntitySearchSerializer


class SearchFilter(BaseHaystackFilterBackend):

    query_builder_class = FilterQueryBuilder
    default_operator = operator.and_


class EntitySearchViewSet(ListModelMixin,ViewSetMixin, HaystackGenericAPIView):
    """
    A generic view to be used for rendering the result list while searching.
    """
    index_models = [EntityModel]

    #renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)
    serializer_class = EntitySearchSerializer  # to be set by SearchView.as_view(serializer_class=...)

    filter_backends = [SearchFilter]


    #def get(self, request, *args, **kwargs):
    #    return self.list(request, *args, **kwargs)
    #
    # def get_template_names(self):
    #     return [self.request.current_page.get_template()]
