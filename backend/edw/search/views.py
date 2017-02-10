# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.mixins import ListModelMixin
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from drf_haystack.generics import HaystackGenericAPIView
from drf_haystack.viewsets import ViewSetMixin

from edw.models.entity import EntityModel
from edw.search.serializers import EntitySearchSerializer


class EntitySearchViewSet(ListModelMixin, ViewSetMixin, HaystackGenericAPIView):
    """
    A generic view to be used for rendering the result list while searching.
    """
    queryset = EntityModel.objects.all()
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer,)
    serializer_class = EntitySearchSerializer  # to be set by SearchView.as_view(serializer_class=...)

    index_models = [EntityModel]

    def get_queryset(self):
        result=super(EntitySearchViewSet, self).get_queryset()
        print('================= result ===============', dir(result))
        print(result.stats_results())
        return result

    #def get(self, request, *args, **kwargs):
    #    return self.list(request, *args, **kwargs)
    #
    # def get_template_names(self):
    #     return [self.request.current_page.get_template()]
