# -*- coding: utf-8 -*-
"""E1: минимальный URLconf для проверки reverse в REST-контракте."""
from __future__ import unicode_literals

from django.http import HttpResponse
from django.urls import include, path
from rest_framework.response import Response
from rest_framework.views import APIView

from edw.rest.permissions import IsOwnerOrStaffOrSuperuser


def _stub_view(request, *args, **kwargs):
    return HttpResponse('ok')


class PermissionProbeView(APIView):
    """
    E4: реальный DRF-view для проверки прав на уровне представления.

    Права намеренно строгие: не-staff и не-суперпользователь получают 403
    даже на чтение — ослабление класса сломает контракт.
    """

    permission_classes = [IsOwnerOrStaffOrSuperuser]

    def get(self, request, *args, **kwargs):
        return Response({'ok': True})

    def post(self, request, *args, **kwargs):
        return Response({'ok': True})


api_urlpatterns = [
    path('contractentity/<int:pk>/', _stub_view, name='contractentity-detail'),
    path('contractentitychild/<int:pk>/', _stub_view, name='contractentitychild-detail'),
    path('datamart/<int:pk>/', _stub_view, name='datamart-detail'),
    path('term/<int:pk>/', _stub_view, name='term-detail'),
    # E4: проверка DRF permissions-потока на установленной версии DRF.
    path('permission-probe/', PermissionProbeView.as_view(), name='permission-probe'),
]

urlpatterns = [
    path('', include((api_urlpatterns, 'edw'), namespace='edw')),
]
