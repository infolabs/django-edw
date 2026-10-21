# -*- coding: utf-8 -*-
"""
E1 test stub: minimal stand-in for djangorestframework-bulk.
"""
from __future__ import unicode_literals

from rest_framework import serializers


class BulkSerializerMixin(object):
    """Marker mixin used by django-edw serializer bases."""


class BulkListSerializer(serializers.ListSerializer):
    """List serializer base used by django-edw serializer bases."""
