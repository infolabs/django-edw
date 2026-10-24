# -*- coding: utf-8 -*-
"""E9/R5: fixtures for the write-alias regression gate."""
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from edw.models.data_mart import DataMartModel
from edw.models.entity import EntityModel


@pytest.fixture(autouse=True)
def reset_edw_caches():
    cache.clear()
    EntityModel._entities_types_cache = None
    EntityModel._content_type_cache = {}
    if hasattr(DataMartModel, '_base_entity_model_cache'):
        DataMartModel._base_entity_model_cache = None
    yield
    cache.clear()
    EntityModel._entities_types_cache = None


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username='r5-root', email='r5-root@example.invalid', password='not-a-secret'
    )


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client
