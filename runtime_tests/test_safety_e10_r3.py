# -*- coding: utf-8 -*-
"""E11/R3 (ported E10.safetycheck): R3 admission/identity/permission before state-aware work."""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term

import safety_probe_views as e10_probe_views

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'
HOOK_URL = '/probe/hook/terms/'
MUTATE_URL = '/probe/mutate/terms/'
PERMISSION_URL = '/probe/permission/terms/'

UNIQUE_ID_MARKERS = ('уже существует', 'already exists')


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def scope():
    scope_root = Term.objects.create(name='Scope root', slug='r3-scope-root')
    other_root = Term.objects.create(name='Other root', slug='r3-other-root')
    target = Term.objects.create(name='Target', slug='r3-target', parent=other_root)
    inside = Term.objects.create(name='Inside', slug='r3-inside', parent=scope_root)
    return scope_root, other_root, target, inside


def _body(response):
    return response.content.decode('utf-8', 'replace')


def test_post_by_existing_in_scope_id_upserts(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': inside.pk, 'name': 'Inside renamed', 'slug': 'r3-inside'}],
        format='json',
    )
    inside.refresh_from_db()
    assert response.status_code in (200, 201), _body(response)[:400]
    assert inside.name == 'Inside renamed'
    assert inside.pk == inside.pk


def test_post_by_forbidden_id_is_refused_before_the_serializer_validator(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': target.pk, 'name': 'Escaped', 'slug': 'r3-target'}],
        format='json',
    )
    target.refresh_from_db()
    body = _body(response).lower()
    assert target.name == 'Target', 'forbidden target modified'
    assert response.status_code == 400, _body(response)[:400]
    assert not any(marker in body for marker in UNIQUE_ID_MARKERS), (
        'a state-aware validator observed the forbidden target: {}'.format(body[:400]))


def test_post_with_unknown_id_is_not_silently_replaced(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': 999999, 'name': 'Ghost', 'slug': 'r3-ghost'}],
        format='json',
    )
    assert not Term.objects.filter(slug='r3-ghost').exists()
    assert response.status_code == 400, _body(response)[:400]


def test_post_with_untyped_id_is_a_validation_error(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': 'not-a-number', 'name': 'Wrong', 'slug': 'r3-wrong'}],
        format='json',
    )
    assert not Term.objects.filter(slug='r3-wrong').exists()
    assert response.status_code == 400, _body(response)[:400]


def test_duplicate_target_in_one_batch_is_refused_without_writes(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [
            {'id': inside.pk, 'name': 'First write', 'slug': 'r3-inside'},
            {'id': inside.pk, 'name': 'Second write', 'slug': 'r3-inside'},
        ],
        format='json',
    )
    inside.refresh_from_db()
    assert inside.name == 'Inside'
    assert response.status_code == 400, _body(response)[:400]


def test_ambiguous_id_and_slug_is_refused_without_writes(operator, scope):
    scope_root, other_root, target, inside = scope
    second_inside = Term.objects.create(
        name='Second inside', slug='r3-second-inside', parent=scope_root)
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': inside.pk, 'name': 'Ambiguous', 'slug': 'r3-second-inside'}],
        format='json',
    )
    inside.refresh_from_db()
    second_inside.refresh_from_db()
    assert inside.name == 'Inside' and second_inside.name == 'Second inside'
    assert response.status_code == 400, _body(response)[:400]


def test_mixed_batch_with_forbidden_identity_is_atomic(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [
            {'id': inside.pk, 'name': 'Allowed update', 'slug': 'r3-inside'},
            {'id': target.pk, 'name': 'Forbidden', 'slug': 'r3-target'},
        ],
        format='json',
    )
    inside.refresh_from_db()
    target.refresh_from_db()
    assert inside.name == 'Inside', 'partial write from a refused batch'
    assert target.name == 'Target'
    assert response.status_code == 400, _body(response)[:400]


def test_supplied_identity_is_the_saved_identity(operator, scope):
    scope_root, other_root, target, inside = scope
    response = operator.post(
        TERMS_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': inside.pk, 'name': 'Same identity', 'slug': 'r3-inside'}],
        format='json',
    )
    assert response.status_code in (200, 201)
    saved = Term.objects.get(pk=inside.pk)
    assert saved.pk == inside.pk and saved.slug == 'r3-inside'


def test_dynamic_field_hook_does_not_see_the_forbidden_target(operator, scope):
    """R3: full to_internal_value must not run a state-aware hook before
    whole-batch admission.

    ``HookProbeTermSerializer.validate_slug`` is the documented DRF/RESTMeta
    dynamic hook shape: it resolves the supplied natural key through the global
    manager.  A batch that addresses a forbidden (out-of-scope) id must be
    refused before that hook can resolve the forbidden target.
    """
    scope_root, other_root, target, inside = scope
    e10_probe_views.HOOK_EVENTS[:] = []
    response = operator.post(
        HOOK_URL + '?parent_id={}'.format(scope_root.pk),
        [{'id': target.pk, 'name': 'Hook probe', 'slug': 'r3-target'}],
        format='json',
    )
    target.refresh_from_db()
    assert target.name == 'Target'
    assert response.status_code == 400, _body(response)[:400]
    assert e10_probe_views.HOOK_EVENTS == [], (
        'a dynamic state-aware hook resolved the forbidden target before admission: {}'.format(
            e10_probe_views.HOOK_EVENTS))


def test_dynamic_validator_cannot_retarget_the_admitted_write(operator, scope):
    """R3: the identity admitted before validation is the identity saved.

    A dynamic ``validate`` hook rewrites the validated natural key after
    admission.  The save must not silently resolve a different existing target
    from the rewritten data; either the originally admitted (new) identity is
    written or the request is refused without writes.
    """
    scope_root, other_root, target, inside = scope
    response = operator.post(
        MUTATE_URL + '?parent_id={}&_e10_mutate_to={}'.format(scope_root.pk, 'r3-inside'),
        [{'name': 'Mutation', 'slug': 'r3-new-slug'}],
        format='json',
    )
    inside.refresh_from_db()
    created = Term.objects.filter(slug='r3-new-slug').first()
    refused = response.status_code >= 400 and inside.name == 'Inside'
    assert created is not None or refused, (
        'the admitted new identity was not saved and the request was not refused: '
        'status={} body={}'.format(response.status_code, _body(response)[:400]))
    assert inside.name == 'Inside', (
        'a dynamic validator retargeted the admitted write onto an existing object: '
        'inside.name={!r} status={}'.format(inside.name, response.status_code))


def test_whole_batch_permission_is_decided_before_any_state_aware_validator(operator, scope):
    """R3: the permission of the complete batch is decided before validators.

    Item 1 is permitted, item 2 is forbidden by an object permission.  A
    whole-batch admission must refuse the batch before any state-aware
    validator runs; a per-item interleaving runs item 1's validator first.
    """
    scope_root, other_root, target, inside = scope
    denied = Term.objects.create(name='Denied', slug='r3-denied', parent=scope_root)
    e10_probe_views.MARKERS[:] = []
    response = operator.post(
        PERMISSION_URL + '?parent_id={}'.format(scope_root.pk),
        [
            {'id': inside.pk, 'name': 'Interleaved update', 'slug': 'r3-inside'},
            {'id': denied.pk, 'name': 'Denied update', 'slug': 'r3-denied'},
        ],
        format='json',
    )
    inside.refresh_from_db()
    denied.refresh_from_db()
    assert inside.name == 'Inside' and denied.name == 'Denied'
    assert response.status_code in (400, 403), _body(response)[:400]
    assert e10_probe_views.MARKERS == [], (
        'state-aware validators ran before the whole-batch permission decision '
        'was complete: {}'.format(e10_probe_views.MARKERS))
