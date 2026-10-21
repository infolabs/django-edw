# -*- coding: utf-8 -*-
"""E1 test stub: DRF filter backend aliases."""
from __future__ import unicode_literals

from rest_framework.filters import BaseFilterBackend


class DjangoFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        return queryset


class RestFrameworkFilterBackend(DjangoFilterBackend):
    pass
