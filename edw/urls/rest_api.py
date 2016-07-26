# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf.urls import url, include
from rest_framework import routers
#from rest_framework.urlpatterns import format_suffix_patterns

#from shop.views.cart import CartViewSet, WatchViewSet
#from shop.views.checkout import CheckoutViewSet
#from edw.views.term import TermSelectView
from edw.views.term import TermViewSet

router = routers.DefaultRouter()
#router.include_format_suffixes = False

router.register(r'terms', TermViewSet, base_name='term')

'''
router.register(r'cart', CartViewSet, base_name='cart')
router.register(r'watch', WatchViewSet, base_name='watch')
router.register(r'checkout', CheckoutViewSet, base_name='checkout')
'''

urlpatterns = (
    #url(r'^selected-terms/$', TermSelectView.as_view(), name='selected-terms'),
    url(r'^', include(router.urls)), #url(r'^api/', include(router.urls, namespace='api')),
)

# Format suffixes
#urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
