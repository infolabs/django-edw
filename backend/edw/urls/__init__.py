# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url
from . import rest_api
try:
    from . import auth
except:
    pass

from ..views.term import RebuildTermTreeView
from ..views.data_mart import RebuildDataMartTreeView


urlpatterns = (
    url(r'^rebuild_term_tree/',
        RebuildTermTreeView.as_view(),
        name='rebuild_term_tree'
    ),
    url(r'^rebuild_datamart_tree/',
        RebuildDataMartTreeView.as_view(),
        name='rebuild_datamart_tree'
    ),
    url(r'^api/', include(rest_api)),
)

try:
    urlpatterns = [
        url(r'^auth/', include(auth)),
    ] + urlpatterns
except NameError:
    pass