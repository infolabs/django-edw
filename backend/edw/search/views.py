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


def more_like_this(request):
    results = []
    text = request.GET.get('q')
    # place IN: geo=65.345,33.987897&q=Sadovaya65
    # OUT: 65.345,33.987897 -geohash-> qwewetwer qwewetwe qwewetw qwewet qwewe

    # entity_model.parce_req(req)



    entity_model = request.GET.get('model')

    # text = entity_model.parce_req(request)

    if text:
        # import pdb; pdb.set_trace()
        print()
        print('-----------------------------------------------')
        print(text)
        print('-----------------------------------------------')

        search_result = get_more_like_this(text, entity_model)
        suggestions = analyze_suggestions(search_result)

        for suggestion in suggestions:
            entity_id = suggestion['category']['django_id']  # Just for detail URL
            # try:
            #     entity = EntityModel.objects.get(id=entity_id)
            # except EntityModel.DoesNotExist:
            #     pass
            # else:
            #     pass
            suggestion_data = {
                'id': entity_id,
                'model': suggestion['category']['django_ct'],
                'title': suggestion['category']['name'],
                'score': suggestion['score'],
                'url': '#'
            }
            results.append(suggestion_data)
    print()
    print()


    return HttpResponse(
        json.dumps({'results': results}),
        content_type='application/json; charset=UTF-8'
    )
