# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http import HttpResponse
from rest_framework.mixins import ListModelMixin

from drf_haystack.generics import HaystackGenericAPIView
from drf_haystack.viewsets import ViewSetMixin

from edw.models.entity import EntityModel
from edw.search.serializers import EntitySearchSerializer
from edw.search.filters import HaystackTermFilter
from edw.search.classify import get_more_like_this, analyze_suggestions


class EntitySearchViewSet(ListModelMixin, ViewSetMixin, HaystackGenericAPIView):
    """
    A generic view to be used for rendering the result list while searching.
    """
    index_models = [EntityModel]

    #renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)
    serializer_class = EntitySearchSerializer  # to be set by SearchView.as_view(serializer_class=...)

    filter_backends = [HaystackTermFilter]


    #def get(self, request, *args, **kwargs):
    #    return self.list(request, *args, **kwargs)
    #
    # def get_template_names(self):
    #     return [self.request.current_page.get_template()]


def more_like_this(request, entity_model=None):
    results = []
    text = request.GET.get('q')
    if text:
        search_result = get_more_like_this(text, entity_model)
        suggestions = analyze_suggestions(search_result)

        for suggestion in suggestions:
            suggestion_data = {
                'id': suggestion['source']['django_id'],
                'model': suggestion['source']['django_ct'],
                'title': suggestion['category'],
                'url': 'https://google.com/',  # TODO
            }
            results.append(suggestion_data)

    return HttpResponse(
        json.dumps({'results': results}),
        content_type='application/json'
    )
