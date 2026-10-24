# -*- coding: utf-8 -*-
"""
E7: routers come from the real InfLabs bulk package, expose list/detail and
collection-level bulk actions, and keep the nested prefix/lookup contract.
"""
from __future__ import unicode_literals

from rest_framework_bulk.routes import BulkRouterMixin

from edw.rest import routers
from edw.views.data_mart import DataMartViewSet
from edw.views.entity import EntityViewSet
from edw.views.term import TermViewSet


BULK_ACTIONS = {
    'put': 'bulk_update',
    'patch': 'partial_bulk_update',
    'delete': 'bulk_destroy',
}


def _routes_by_name(router):
    return {url.name: url for url in router.urls}


def test_bulk_router_mixin_is_the_real_provider_class():
    assert BulkRouterMixin.__module__ == 'rest_framework_bulk.routes'
    for router_class in (routers.DefaultBulkRouter, routers.NestedSimpleBulkRouter):
        assert issubclass(router_class, BulkRouterMixin)


def test_viewsets_use_real_bulk_model_viewset():
    from rest_framework_bulk.generics import BulkModelViewSet

    for viewset in (TermViewSet, DataMartViewSet, EntityViewSet):
        assert issubclass(viewset, BulkModelViewSet)
        assert BulkModelViewSet.__module__ == 'rest_framework_bulk.generics'


def test_collection_bulk_and_detail_routes():
    from edw.urls import rest_api

    routes = _routes_by_name(rest_api.router)
    basenames = (
        'term',
        'datamart',
        EntityViewSet.queryset.model._meta.model_name,
    )
    for basename in basenames:
        collection = routes['{}-list'.format(basename)]
        detail = routes['{}-detail'.format(basename)]
        for method, action in BULK_ACTIONS.items():
            assert collection.callback.actions[method] == action, (basename, method)
        assert detail.callback.actions['get'] == 'retrieve'
        assert detail.callback.actions['put'] == 'update'
        assert detail.callback.actions['delete'] == 'destroy'
        # A collection PUT/PATCH/DELETE must not be routed through the detail
        # actions, and vice versa.
        assert 'retrieve' not in collection.callback.actions.values()


def test_nested_router_keeps_parent_prefix_and_lookup():
    from edw.urls import rest_api

    patterns = [url.pattern.regex.pattern for url in rest_api.data_mart_nested_router.urls]
    assert patterns, 'nested data-mart router has no routes'
    assert any(r'^data-marts/(?P<data_mart_pk>[^/.]+)/entities/$' in pattern or
               r'^data-marts/(?P<data_mart_pk>[^/.]+)/entities/$' == pattern
               for pattern in patterns), patterns
    for url in rest_api.data_mart_nested_router.urls:
        if url.name == 'data-mart-entity-list':
            assert url.callback.actions['put'] == 'bulk_update'
            assert url.callback.actions['delete'] == 'bulk_destroy'
            break
    else:  # pragma: no cover - the route is an explicit contract
        raise AssertionError('data-mart-entity-list route is missing')
