# -*- coding: utf-8 -*-
"""
E9/R5: one write alias for the whole bulk chain, or an early fail-closed
refusal before validators and before the first write.

Real routers and a real second database alias are used; nothing here patches
``router.db_for_write`` or the provider guard.  The two cases are:

* read and write routers agree on ``second``: the complete bulk POST/upsert
  chain (admission, validators, atomic block and save) uses that one alias and
  the row is written there only;
* a read replica diverts reads while writes stay on ``default``: the write is
  refused with ``ImproperlyConfigured`` *before* validation and before any row
  is written.  Reads remain available.  Distributed atomicity is not claimed.
"""
from __future__ import unicode_literals

import pytest
from django.core.exceptions import ImproperlyConfigured

from edw.models.defaults.term import Term

pytestmark = pytest.mark.django_db(transaction=True, databases=['default', 'second'])

TERMS_URL = '/edw/api/terms/'


def test_bulk_post_upsert_uses_the_configured_write_alias(api_client, superuser):
    import safety_alias_router

    safety_alias_router.TermSecondAliasRouter.route_all = True
    try:
        api_client.force_authenticate(user=superuser)
        Term.objects.using('second').create(name='Second only', slug='r5-second-only')
        response = api_client.post(
            TERMS_URL,
            [{'name': 'Second renamed', 'slug': 'r5-second-only'}],
            format='json',
        )
        second_name = Term.objects.using('second').get(slug='r5-second-only').name
        default_leak = Term.objects.using('default').filter(slug='r5-second-only').exists()
        assert second_name == 'Second renamed', (
            'the bulk unit did not update the routed write alias'
        )
        assert not default_leak, (
            'the bulk unit wrote to a database other than the routed write alias'
        )
        assert response.status_code in (200, 201), (
            'bulk upsert on a configured write alias failed: {} {}'.format(
                response.status_code, response.content[:400]
            )
        )
    finally:
        safety_alias_router.TermSecondAliasRouter.route_all = False


def test_read_replica_fails_closed_before_validation_and_write(api_client, superuser):
    import safety_alias_router

    safety_alias_router.ReadReplicaRouter.route_all = True
    try:
        api_client.force_authenticate(user=superuser)
        with pytest.raises(ImproperlyConfigured):
            api_client.post(
                TERMS_URL,
                [{'name': 'Replica-safe', 'slug': 'r5-replica-safe'}],
                format='json',
            )
        default_leak = Term.objects.using('default').filter(slug='r5-replica-safe').exists()
        replica_leak = Term.objects.using('second').filter(slug='r5-replica-safe').exists()
        assert not default_leak and not replica_leak, (
            'a refused bulk write reached a database'
        )
        # Reads are still served through the read router.
        response = api_client.get(TERMS_URL)
        assert response.status_code == 200
    finally:
        safety_alias_router.ReadReplicaRouter.route_all = False


def test_read_replica_fails_closed_for_bulk_update_and_delete(api_client, superuser):
    import safety_alias_router

    term = Term.objects.using('default').create(name='Keep me', slug='r5-keep-me')
    safety_alias_router.ReadReplicaRouter.route_all = True
    try:
        api_client.force_authenticate(user=superuser)
        with pytest.raises(ImproperlyConfigured):
            api_client.patch(
                TERMS_URL,
                [{'id': term.pk, 'name': 'Changed'}],
                format='json',
            )
        with pytest.raises(ImproperlyConfigured):
            api_client.delete(TERMS_URL + '?parent_id=null')
        default_name = Term.objects.using('default').get(pk=term.pk).name
        default_exists = Term.objects.using('default').filter(pk=term.pk).exists()
        assert default_name == 'Keep me'
        assert default_exists
    finally:
        safety_alias_router.ReadReplicaRouter.route_all = False
