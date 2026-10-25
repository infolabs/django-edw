# -*- coding: utf-8 -*-
"""E7/E11: shared fixtures of the real-runtime gate."""
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient

import safety_probe_router
from edw.tests.safety_evidence import write_post_suite_evidence

from edw.models.data_mart import DataMartModel
from edw.models.entity import EntityModel


@pytest.fixture(autouse=True)
def reset_alias_routers():
    """Every test starts and ends with the write-alias routers inert."""
    safety_probe_router.reset_all()
    yield
    safety_probe_router.reset_all()


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
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


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


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Record post-suite in-interpreter evidence (E11/R6)."""
    write_post_suite_evidence(exitstatus)
