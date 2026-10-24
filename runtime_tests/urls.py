# -*- coding: utf-8 -*-
"""E7: URLconf of the real-runtime gate (the real EDW REST router)."""
from __future__ import unicode_literals

from django.urls import include, path

urlpatterns = [
    path('edw/api/', include('edw.urls.rest_api')),
]
