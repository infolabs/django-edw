# -*- coding: utf-8 -*-
"""E7: shared fixtures of the real-runtime gate."""
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

from edw.models.data_mart import DataMartModel
from edw.models.entity import EntityModel


@pytest.fixture(autouse=True)
def reset_edw_caches():
    """Drop EDW class-level caches between tests (locmem cache backend)."""
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
        username='runtime-root', email='runtime-root@example.invalid', password='not-a-secret'
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username='runtime-user', email='runtime-user@example.invalid', password='not-a-secret'
    )


@pytest.fixture
def entity_types(db):
    """
    Materialize the entity-type term tree (normally built by AppConfig.ready()
    in a real deployment; the synthetic app only warms the cache).
    """
    from edw.models.defaults.term import Term

    EntityModel._validate_term_model_cache = {}
    root = EntityModel.materialized
    for clazz in [root] + list(root.get_all_subclasses()):
        clazz.validate_term_model()
    return {
        'root': Term.objects.get(slug=root.__name__.lower()),
        'child': Term.objects.get(slug='contractentitychild'),
    }
