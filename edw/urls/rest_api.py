# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
#from django.conf import settings

from rest_framework_nested import routers

from edw.views.term import TermViewSet
from edw.views.data_mart import DataMartViewSet


router = routers.DefaultRouter()

router.register(r'data-marts', DataMartViewSet)
router.register(r'terms', TermViewSet)

data_mart_terms_router = routers.NestedSimpleRouter(router, r'data-marts', lookup='data_mart')
data_mart_terms_router.register(r'terms', TermViewSet, base_name='data-mart-terms')


'''
if settings.DEBUG:
    router.register(r'customers', CustomerViewSet)
'''

urlpatterns = (
    url(r'^', include(router.urls, namespace='edw')),
    url(r'^', include(data_mart_terms_router.urls, namespace='edw')),
)
