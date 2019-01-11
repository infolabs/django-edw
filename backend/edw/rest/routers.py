# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function


from rest_framework_nested.routers import DefaultRouter, NestedSimpleRouter

from rest_framework_bulk.routes import BulkRouterMixin


__all__ = [
    'BulkRouterMixin',
    'DefaultBulkRouter',
    'NestedSimpleBulkRouter',
    'DefaultRouter',
    'NestedSimpleRouter'
]


class DefaultBulkRouter(BulkRouterMixin, DefaultRouter):
    pass


class NestedSimpleBulkRouter(BulkRouterMixin, NestedSimpleRouter):
    pass
