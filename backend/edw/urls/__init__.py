# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import include, url
from . import rest_api
from . import auth

from ..views.term import RebuildTreeView


urlpatterns = (
    url(r'^rebuild_tree/',
        RebuildTreeView.as_view(),
        name='rebuild_tree'
    ),
    url(r'^api/', include(rest_api)),
    url(r'^auth/', include(auth)),
)
