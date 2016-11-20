# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.exceptions import ImproperlyConfigured
from django.conf.urls import url, include

from rest_framework_nested import routers

from edw.views.term import TermViewSet
from edw.views.data_mart import DataMartViewSet
from edw.views.entity import EntityViewSet, EntitySubjectViewSet

from rest_framework.urlpatterns import format_suffix_patterns


#==============================================================================
# routers
#==============================================================================
router = routers.DefaultRouter()

router.register(r'data-marts', DataMartViewSet)
router.register(r'terms', TermViewSet)
router.register(r'entities', EntityViewSet)

data_mart_nested_router = routers.NestedSimpleRouter(router, r'data-marts', lookup='data_mart')
data_mart_nested_router.register(r'children', DataMartViewSet, base_name='data-mart-children')
data_mart_nested_router.register(r'terms', TermViewSet, base_name='data-mart-term')
data_mart_nested_router.register(r'entities', EntityViewSet, base_name='data-mart-entity')

term_nested_router = routers.NestedSimpleRouter(router, r'terms', lookup='term')
term_nested_router.register(r'children', TermViewSet, base_name='term-children')

entity_nested_router = routers.NestedSimpleRouter(router, r'entities', lookup='entity')
entity_nested_router.register(r'subj', EntitySubjectViewSet, base_name='entity-by-subject')

data_mart_entity_nested_router = routers.NestedSimpleRouter(data_mart_nested_router, r'entities', lookup='entity')
data_mart_entity_nested_router.register(r'subj', EntitySubjectViewSet, base_name='data-mart-entity-by-subject')

try:
    from edw.models.related import DataMartImageModel
    DataMartImageModel() # Test pass if model materialized

    from edw.views.related.data_mart_image import DataMartImageViewSet

    router.register(r'data-marts-images', DataMartImageViewSet)
    data_mart_nested_router.register(r'images', DataMartImageViewSet, base_name='entity-image')
except ImproperlyConfigured:
    pass

try:
    from edw.models.related import EntityImageModel
    EntityImageModel() # Test pass if model materialized

    from edw.views.related.entity_image import EntityImageViewSet

    router.register(r'entities-images', EntityImageViewSet)
    entity_nested_router.register(r'images', EntityImageViewSet, base_name='entity-image')
except ImproperlyConfigured:
    pass


#==============================================================================
# urls
#==============================================================================
edw_patterns = ([
    url(r'^', include(router.urls)),
    url(r'^', include(format_suffix_patterns(data_mart_nested_router.urls))),
    url(r'^', include(format_suffix_patterns(term_nested_router.urls))),
    url(r'^', include(format_suffix_patterns(entity_nested_router.urls))),
    url(r'^', include(format_suffix_patterns(data_mart_entity_nested_router.urls)))
], 'edw')

urlpatterns = [
    url(r'^', include(edw_patterns)),
]
