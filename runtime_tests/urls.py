# -*- coding: utf-8 -*-
"""E7/E11: URLconf of the real-runtime gate (real EDW REST router + probes)."""
from __future__ import unicode_literals

from django.urls import include, path

from edw.rest import routers

from safety_probe_views import (
    HookProbeTermViewSet,
    MutatingTermViewSet,
    PermissionProbeDataMartViewSet,
    PermissionProbeTermViewSet,
    QuerysetBoundTermViewSet,
    RecordingTermViewSet,
    WritableEntityViewSet,
)

urlpatterns = [
    path('edw/api/', include('edw.urls.rest_api')),
]

_probe_router = routers.DefaultBulkRouter()
_probe_router.register('terms', RecordingTermViewSet, basename='probe-term')
urlpatterns += [path('probe/', include(_probe_router.urls))]

_hook_router = routers.DefaultBulkRouter()
_hook_router.register('terms', HookProbeTermViewSet, basename='probe-hook-term')
urlpatterns += [path('probe/hook/', include(_hook_router.urls))]

_mutate_router = routers.DefaultBulkRouter()
_mutate_router.register('terms', MutatingTermViewSet, basename='probe-mutate-term')
urlpatterns += [path('probe/mutate/', include(_mutate_router.urls))]

_permission_router = routers.DefaultBulkRouter()
_permission_router.register('terms', PermissionProbeTermViewSet, basename='probe-permission-term')
urlpatterns += [path('probe/permission/', include(_permission_router.urls))]

_mart_permission_router = routers.DefaultBulkRouter()
_mart_permission_router.register(
    'data-marts', PermissionProbeDataMartViewSet, basename='probe-permission-mart')
urlpatterns += [path('probe/', include(_mart_permission_router.urls))]

_bound_router = routers.DefaultBulkRouter()
_bound_router.register('terms', QuerysetBoundTermViewSet, basename='probe-bound-term')
urlpatterns += [path('probe/bound/', include(_bound_router.urls))]

_entity_router = routers.DefaultBulkRouter()
_entity_router.register('entities', WritableEntityViewSet, basename='probe-entity')
urlpatterns += [path('probe/', include(_entity_router.urls))]
