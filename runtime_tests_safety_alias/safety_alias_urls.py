# -*- coding: utf-8 -*-
"""E9/R5: URLconf for the write-alias regression gate (real EDW router only)."""
from __future__ import unicode_literals

from django.urls import include, path

urlpatterns = [
    path('edw/api/', include('edw.urls.rest_api')),
]
