# -*- coding: utf-8 -*-
"""E11/R5 (ported E10.safetycheck + residual controls): one write alias."""
from __future__ import unicode_literals

import pytest
from django.core.exceptions import ImproperlyConfigured

from edw.models.defaults.term import Term

import safety_probe_router
import safety_probe_views

pytestmark = pytest.mark.django_db(transaction=True, databases=['default', 'second'])

TERMS_URL = '/edw/api/terms/'
PROBE_TERMS_URL = '/probe/terms/'
BOUND_TERMS_URL = '/probe/bound/terms/'


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def route_all_second():
    safety_probe_router.TermSecondAliasRouter.route_all = True
    try:
        yield
    finally:
        safety_probe_router.TermSecondAliasRouter.route_all = False


@pytest.fixture
def read_replica():
    safety_probe_router.ReadReplicaRouter.route_all = True
    try:
        yield
    finally:
        safety_probe_router.ReadReplicaRouter.route_all = False


@pytest.fixture
def explicit_write_default():
    safety_probe_router.ExplicitWriteDefaultRouter.enabled = True
    try:
        yield
    finally:
        safety_probe_router.ExplicitWriteDefaultRouter.enabled = False


@pytest.fixture
def instance_hint_write():
    safety_probe_router.InstanceHintWriteRouter.enabled = True
    try:
        yield
    finally:
        safety_probe_router.InstanceHintWriteRouter.enabled = False


def test_second_alias_bulk_upsert_uses_only_second(operator, route_all_second):
    Term.objects.using('second').create(name='Second only', slug='r5-second-only')
    response = operator.post(
        TERMS_URL, [{'name': 'Second renamed', 'slug': 'r5-second-only'}], format='json')
    assert response.status_code in (200, 201), response.content[:400]
    assert Term.objects.using('second').get(slug='r5-second-only').name == 'Second renamed'
    assert not Term.objects.using('default').filter(slug='r5-second-only').exists(), (
        'bulk upsert wrote to default although the write alias is second')


def test_second_alias_bulk_create_with_parent_uses_only_second(operator, route_all_second):
    parent = Term.objects.using('second').create(name='Second parent', slug='r5-second-parent')
    response = operator.post(
        TERMS_URL,
        [{'name': 'Second child', 'slug': 'r5-second-child', 'parent_id': parent.pk}],
        format='json',
    )
    assert response.status_code == 201, response.content[:400]
    created = Term.objects.using('second').filter(slug='r5-second-child').first()
    assert created is not None and created.parent_id == parent.pk
    assert not Term.objects.using('default').filter(slug='r5-second-child').exists(), (
        'bulk create wrote the child to default')


def test_second_alias_detail_patch_uses_only_second(operator, route_all_second):
    term = Term.objects.using('second').create(name='Detail second', slug='r5-detail-second')
    response = operator.patch(
        TERMS_URL + '{}/'.format(term.pk), {'name': 'Detail renamed'}, format='json')
    assert response.status_code in (200, 204), response.content[:400]
    assert Term.objects.using('second').get(pk=term.pk).name == 'Detail renamed'
    assert not Term.objects.using('default').filter(pk=term.pk).exists(), (
        'detail patch wrote to default although the write alias is second')


def test_read_replica_refuses_bulk_post_before_any_validator(operator, read_replica):
    safety_probe_views.MARKERS[:] = []
    with pytest.raises(ImproperlyConfigured):
        operator.post(
            PROBE_TERMS_URL, [{'name': 'Replica refused', 'slug': 'r5-replica-refused'}],
            format='json')
    assert safety_probe_views.MARKERS == [], (
        'a state-aware validator ran before the read-replica refusal: {}'.format(
            safety_probe_views.MARKERS))
    assert not Term.objects.using('default').filter(slug='r5-replica-refused').exists()
    assert not Term.objects.using('second').filter(slug='r5-replica-refused').exists()


def test_read_replica_refuses_bulk_update_and_delete(operator, read_replica):
    term = Term.objects.using('default').create(name='Keep me', slug='r5-keep-me')
    with pytest.raises(ImproperlyConfigured):
        operator.patch(
            PROBE_TERMS_URL, [{'id': term.pk, 'name': 'Changed'}], format='json')
    with pytest.raises(ImproperlyConfigured):
        operator.delete(PROBE_TERMS_URL + '?parent_id=null')
    assert Term.objects.using('default').filter(pk=term.pk).exists()
    assert Term.objects.using('default').get(pk=term.pk).name == 'Keep me'


def test_detail_patch_under_read_replica_is_fail_closed(operator, read_replica):
    """R5: validation may not silently read the replica and write the replica.

    The write router selects ``default``; a divergent read router is not a
    supported configuration, so the request must be refused before validation
    and before the first write.  No alias may receive a row change.
    """
    term = Term.objects.using('default').create(name='Primary', slug='r5-primary')
    Term.objects.using('second').create(id=term.pk, name='Replica', slug='r5-primary')
    response = operator.patch(
        TERMS_URL + '{}/'.format(term.pk), {'name': 'Patched'}, format='json')
    default_name = Term.objects.using('default').get(pk=term.pk).name
    replica_name = Term.objects.using('second').get(pk=term.pk).name
    assert replica_name == 'Replica', (
        'detail PATCH wrote the read-replica alias while db_for_write selected default: '
        'default={!r} replica={!r} status={}'.format(
            default_name, replica_name, response.status_code))
    assert default_name == 'Primary', (
        'detail PATCH validated against the replica and wrote default silently: '
        'default={!r} replica={!r} status={}'.format(
            default_name, replica_name, response.status_code))


def test_detail_delete_under_read_replica_is_fail_closed(operator, read_replica):
    """R5: the delete effect set may not be authorized on the replica and
    executed there while the write router selects ``default``."""
    term = Term.objects.using('default').create(name='Doomed', slug='r5-doomed')
    Term.objects.using('second').create(id=term.pk, name='Doomed', slug='r5-doomed')
    response = operator.delete(TERMS_URL + '{}/'.format(term.pk))
    default_left = Term.objects.using('default').filter(pk=term.pk).exists()
    replica_left = Term.objects.using('second').filter(pk=term.pk).exists()
    assert default_left, (
        'detail DELETE authorized on the replica deleted the default row: status={}'.format(
            response.status_code))
    assert replica_left, (
        'detail DELETE wrote the read-replica alias while db_for_write selected default: '
        'status={}'.format(response.status_code))


def test_explicit_write_default_with_second_read_is_refused(operator, explicit_write_default):
    """R5: an *explicit* write alias diverging from the read alias is refused.

    This is the explicit router variant (``db_for_write`` returns ``'default'``,
    not ``None``): the detail write must be refused before validators and before
    the first write, and the bulk path must refuse with ``ImproperlyConfigured``.
    """
    term = Term.objects.using('default').create(name='Explicit', slug='r5-explicit')
    response = operator.patch(
        TERMS_URL + '{}/'.format(term.pk), {'name': 'Changed'}, format='json')
    assert Term.objects.using('default').get(pk=term.pk).name == 'Explicit'
    assert not Term.objects.using('second').filter(pk=term.pk).exists()
    assert response.status_code == 400, response.content[:400]

    with pytest.raises(ImproperlyConfigured):
        operator.post(
            PROBE_TERMS_URL, [{'name': 'Explicit bulk', 'slug': 'r5-explicit-bulk'}],
            format='json')
    assert not Term.objects.using('default').filter(slug='r5-explicit-bulk').exists()
    assert not Term.objects.using('second').filter(slug='r5-explicit-bulk').exists()


def test_instance_hint_write_is_refused(operator, instance_hint_write):
    """R5: ``write=None`` + instance hint must not move the write alias.

    Both class-level router answers are ``default``; only
    ``db_for_write(Model, instance=obj)`` returns ``second``.  The guard must
    refuse instead of letting the model save follow the hint.
    """
    term = Term.objects.using('default').create(name='Hinted', slug='r5-hinted')
    response = operator.patch(
        TERMS_URL + '{}/'.format(term.pk), {'name': 'Moved'}, format='json')
    assert Term.objects.using('default').get(pk=term.pk).name == 'Hinted', (
        'an instance hint silently moved the write authority'
    )
    assert not Term.objects.using('second').filter(pk=term.pk).exists(), (
        'the instance-hinted write reached the second alias'
    )
    assert response.status_code == 400, response.content[:400]


def test_queryset_bound_view_is_refused(operator):
    """R5: ``queryset._db`` must not replace the router-selected authority."""
    term = Term.objects.using('second').create(name='Bound', slug='r5-bound')
    response = operator.patch(
        BOUND_TERMS_URL + '{}/'.format(term.pk), {'name': 'Changed'}, format='json')
    assert Term.objects.using('second').get(pk=term.pk).name == 'Bound'
    assert not Term.objects.using('default').filter(pk=term.pk).exists()
    assert response.status_code == 400, response.content[:400]

    with pytest.raises(ImproperlyConfigured):
        operator.post(
            BOUND_TERMS_URL, [{'name': 'Bound bulk', 'slug': 'r5-bound-bulk'}],
            format='json')
    assert not Term.objects.using('default').filter(slug='r5-bound-bulk').exists()
    assert not Term.objects.using('second').filter(slug='r5-bound-bulk').exists()


def test_detail_put_under_read_replica_is_fail_closed(operator, read_replica):
    """R5: the detail PUT path uses the same single-write-alias guard."""
    term = Term.objects.using('default').create(name='Put primary', slug='r5-put')
    Term.objects.using('second').create(id=term.pk, name='Put replica', slug='r5-put')
    response = operator.put(
        TERMS_URL + '{}/'.format(term.pk),
        {'name': 'Put changed', 'slug': 'r5-put'}, format='json')
    default_name = Term.objects.using('default').get(pk=term.pk).name
    replica_name = Term.objects.using('second').get(pk=term.pk).name
    assert default_name == 'Put primary', (
        'detail PUT wrote default while the read alias diverged: {!r}'.format(default_name))
    assert replica_name == 'Put replica', (
        'detail PUT wrote the replica alias: {!r}'.format(replica_name))
    assert response.status_code == 400, response.content[:400]
