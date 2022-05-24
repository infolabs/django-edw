# -*- coding: utf-8 -*-
try:
    from rest_framework_filters.backends import DjangoFilterBackend
except ImportError:
    from rest_framework_filters.backends import RestFrameworkFilterBackend as DjangoFilterBackend


class EDWFilterBackend(DjangoFilterBackend):
    pass
