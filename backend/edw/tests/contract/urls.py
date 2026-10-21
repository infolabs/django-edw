# -*- coding: utf-8 -*-
"""E1: минимальный URLconf для проверки reverse в REST-контракте."""
from __future__ import unicode_literals

from django.http import HttpResponse
from django.urls import include, path


def _stub_view(request, *args, **kwargs):
    return HttpResponse('ok')


api_urlpatterns = [
    path('contractentity/<int:pk>/', _stub_view, name='contractentity-detail'),
    path('contractentitychild/<int:pk>/', _stub_view, name='contractentitychild-detail'),
    path('datamart/<int:pk>/', _stub_view, name='datamart-detail'),
    path('term/<int:pk>/', _stub_view, name='term-detail'),
]

urlpatterns = [
    path('', include((api_urlpatterns, 'edw'), namespace='edw')),
]
