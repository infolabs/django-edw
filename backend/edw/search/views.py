# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.http import JsonResponse
from django.apps import apps

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
    """
    Классификатор объектов
    :param request: запрос
    :return:
    """
    # имя модели в которой производится поиск
    # Пример: m=nash_region.particularproblem
    model = request.GET.get('m', None)

    model_class = EntityModel
    if model is not None:
        try:
            model_class = apps.get_model(*str(model).rsplit(".", 1))
        except LookupError:
            model = None


    search_query = model_class.get_search_query(request)

    # for development purposes only
    # print('========================')
    # print(search_query)
    # print()

    results = []
    if search_query:
        search_result = get_more_like_this(search_query.pop('like'), model=model, **search_query)
        suggestions = analyze_suggestions(search_result)

        for suggestion in suggestions:
            category = suggestion['category']
            pk = category.get('id', None)
            model, url = None, None
            if pk is not None:
                try:
                    obj = EntityModel.objects.get(id=pk)
                except EntityModel.DoesNotExist:
                    pass
                else:
                    model = obj._meta.object_name.lower()
                    url = obj.get_absolute_url(request=request)

            suggestion_data = {
                'id': pk,
                'model': model,
                'title': category['name'],
                'score': suggestion['score'],
                'confidience': suggestion['confidience'],
                'words': suggestion['words'],
                'url': url
            }
            results.append(suggestion_data)

    return JsonResponse({
        'results': results
    })
