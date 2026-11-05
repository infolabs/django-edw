# -*- coding: utf-8 -*-
"""E12.residualcheck: independent URLconf (product REST API + check probes)."""
from __future__ import unicode_literals

from django.urls import include, path

from edw.rest import routers

import e12_views as probes

urlpatterns = [
    path('edw/api/', include('edw.urls.rest_api')),
]


def _mount(prefix, routes):
    router = routers.DefaultBulkRouter()
    for resource, viewset, basename in routes:
        router.register(resource, viewset, basename=basename)
    urlpatterns.append(path(prefix, include(router.urls)))


_mount('e12/rec/', [('terms', probes.RecordingTermViewSet, 'e12-rec-term')])
_mount('e12/hook/', [('terms', probes.HookTermViewSet, 'e12-hook-term')])
_mount('e12/mutate/', [('terms', probes.MutateTermViewSet, 'e12-mutate-term')])
_mount('e12/permission/', [('terms', probes.PermissionTermViewSet,
                            'e12-permission-term')])
_mount('e12/bound/', [('terms', probes.BoundTermViewSet, 'e12-bound-term')])
_mount('e12/entities/', [('entities', probes.WritableEntityViewSet,
                          'e12-entity')])
_mount('e12/datamarts/', [('data-marts', probes.RecordingDataMartViewSet,
                           'e12-datamart')])
