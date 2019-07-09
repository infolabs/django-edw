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
    """
    ENG: This router includes routes for the standard set of list, create, 
    retrieve, update, partial_update and destroy actions, but additionally 
    includes a default API root view, that returns a response containing hyperlinks 
    to all the list views.
    RUS: Маршрутизатор, содержащий маршруты для стандартного набора
    и дополнительно включает в себя корневое представление API по умолчанию.
    """
    pass


class NestedSimpleBulkRouter(BulkRouterMixin, NestedSimpleRouter):
    """
     ENG: Router and relationship fields for working with nested resources
     RUS: Маршрутизатор и поля отношений для работы с вложенными ресурсами
     """
    pass
