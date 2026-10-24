# -*- coding: utf-8 -*-
"""
E9/R3: typed lookups, scoped target and batch permission happen before the
state-aware validators, and the admitted identity is the saved identity.

Ports the E8 counter-examples into the product regression gate:

* bulk POST by an existing in-scope ``id`` upserts instead of failing in
  ``full_clean(validate_unique=True)``;
* a forbidden target never reaches the state-aware validator (no "already
  exists" error and no modification);
* an unknown ``id`` is refused instead of being silently replaced by a create;
* an untyped lookup is a validation error, not a server error.
"""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'

UNIQUE_ID_MARKERS = ('уже существует', 'already exists')


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def scoped_target():
    scope_root = Term.objects.create(name='Scope root', slug='r3-scope-root')
    other_root = Term.objects.create(name='Other root', slug='r3-other-root')
    target = Term.objects.create(name='Target', slug='r3-target', parent=other_root)
    inside = Term.objects.create(name='Inside', slug='r3-inside', parent=scope_root)
    return scope_root, other_root, target, inside


def _body(response):
    return response.content.decode('utf-8', 'replace')


def test_post_by_existing_id_upserts_inside_scope(operator, scoped_target):
    scope_root, other_root, target, inside = scoped_target
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': inside.pk, 'name': 'Inside renamed', 'slug': 'r3-inside'}],
        format='json',
    )
    inside.refresh_from_db()
    assert inside.name == 'Inside renamed'
    assert response.status_code in (200, 201), _body(response)[:500]


def test_post_by_forbidden_id_is_refused_before_the_validator(operator, scoped_target):
    scope_root, other_root, target, inside = scoped_target
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': target.pk, 'name': 'Escaped', 'slug': 'r3-target'}],
        format='json',
    )
    target.refresh_from_db()
    body = _body(response).lower()
    assert target.name == 'Target'
    assert response.status_code == 400, _body(response)[:500]
    assert not any(marker in body for marker in UNIQUE_ID_MARKERS), (
        'a state-aware validator observed the forbidden target: {}'.format(_body(response)[:500])
    )


def test_post_with_unknown_id_is_not_silently_replaced(operator, scoped_target):
    scope_root, other_root, target, inside = scoped_target
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': 999999, 'name': 'Ghost', 'slug': 'r3-ghost'}],
        format='json',
    )
    assert not Term.objects.filter(slug='r3-ghost').exists(), (
        'supplied id 999999 was silently dropped and a new object was created'
    )
    assert response.status_code == 400, _body(response)[:500]


def test_post_with_untyped_lookup_is_a_validation_error(operator, scoped_target):
    scope_root, other_root, target, inside = scoped_target
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': 'not-a-number', 'name': 'Wrong type', 'slug': 'r3-wrong-type'}],
        format='json',
    )
    assert not Term.objects.filter(slug='r3-wrong-type').exists()
    assert response.status_code == 400, _body(response)[:500]


def test_supplied_identity_is_the_saved_identity(operator, scoped_target):
    scope_root, other_root, target, inside = scoped_target
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': inside.pk, 'name': 'Same identity', 'slug': 'r3-inside'}],
        format='json',
    )
    assert response.status_code in (200, 201)
    saved = Term.objects.get(pk=inside.pk)
    assert saved.pk == inside.pk
    assert saved.slug == 'r3-inside'
