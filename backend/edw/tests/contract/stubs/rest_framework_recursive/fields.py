# -*- coding: utf-8 -*-
"""
E1 test stub: minimal stand-in for djangorestframework-recursive.

Recursive tree serialization is out of the E1 contract scope; only class
construction and field declaration need to work.
"""
from __future__ import unicode_literals

from rest_framework import serializers


class RecursiveField(serializers.Field):
    """Placeholder recursive field (never serialized in contract tests)."""

    def to_representation(self, value):
        return None

    def to_internal_value(self, data):
        return data
