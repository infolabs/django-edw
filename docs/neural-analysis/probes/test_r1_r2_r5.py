# -*- coding: utf-8 -*-
"""E12.residualcheck: independent R5 write-alias controls, R1/R2 regressions."""
from __future__ import unicode_literals

import pytest

import e12_routers
from edw.models.defaults.term import Term
from edw.models.data_mart import DataMartModel
from edw.tests.contract.app.models import DataMart
from edw.rest.viewsets import (
    BulkDestroyPolicyMixin,
    SingleWriteAliasGuardMixin,
)
from edw.views.data_mart import DataMartViewSet
from edw.views.entity import EntityViewSet
from edw.views.term import TermViewSet

pytestmark = pytest.mark.django_db(transaction=True, databases=['default', 'second'])

TERMS = '/edw/api/terms/'


def term_states(alias):
    return {
        t.pk: (t.name, t.slug, t.parent_id)
        for t in Term.objects.using(alias).all()
    }


@pytest.fixture
def both_alias_term():
    """Same pk present on both aliases, different names."""
    t = Term.objects.using('default').create(name='Primary', slug='e12-alias-x')
    Term.objects.using('second').create(id=t.pk, name='Replica', slug='e12-alias-x')
    return t


def test_guard_mixins_present_in_viewsets():
    assert SingleWriteAliasGuardMixin in TermViewSet.__mro__
    assert SingleWriteAliasGuardMixin in DataMartViewSet.__mro__
    assert SingleWriteAliasGuardMixin in EntityViewSet.__mro__
    assert BulkDestroyPolicyMixin in TermViewSet.__mro__
    assert BulkDestroyPolicyMixin in DataMartViewSet.__mro__
    assert BulkDestroyPolicyMixin in EntityViewSet.__mro__


def test_consistent_second_alias_bulk_create(operator):
    e12_routers.SecondAliasRouter.enabled = True
    try:
        parent = Term.objects.using('second').create(
            name='Second parent', slug='e12-second-parent')
        response = operator.post(
            TERMS,
            [{'name': 'Second child', 'slug': 'e12-second-child',
              'parent_id': parent.pk}],
            format='json',
        )
    finally:
        e12_routers.SecondAliasRouter.enabled = False
    assert response.status_code == 201, response.content[:400]
    child = Term.objects.using('second').filter(slug='e12-second-child').first()
    assert child is not None and child.parent_id == parent.pk
    assert not Term.objects.using('default').filter(
        slug='e12-second-child').exists()


def test_consistent_second_alias_detail_patch(operator):
    e12_routers.SecondAliasRouter.enabled = True
    try:
        term = Term.objects.using('second').create(
            name='Detail second', slug='e12-second-detail')
        response = operator.patch(
            TERMS + '{}/'.format(term.pk), {'name': 'Second renamed'},
            format='json')
    finally:
        e12_routers.SecondAliasRouter.enabled = False
    assert response.status_code in (200, 204), response.content[:400]
    assert Term.objects.using('second').get(pk=term.pk).name == 'Second renamed'
    assert not Term.objects.using('default').filter(pk=term.pk).exists()


def test_read_replica_detail_patch_refused_before_write(operator, both_alias_term):
    e12_routers.ReadReplicaRouter.enabled = True
    try:
        before_d = term_states('default')
        before_s = term_states('second')
        response = operator.patch(
            TERMS + '{}/'.format(both_alias_term.pk),
            {'name': 'Patched'}, format='json')
    finally:
        e12_routers.ReadReplicaRouter.enabled = False
    assert response.status_code == 400, response.content[:400]
    assert term_states('default') == before_d, 'default alias changed'
    assert term_states('second') == before_s, 'replica alias changed'


def test_read_replica_detail_delete_refused(operator, both_alias_term):
    e12_routers.ReadReplicaRouter.enabled = True
    try:
        before_d = term_states('default')
        before_s = term_states('second')
        response = operator.delete(TERMS + '{}/'.format(both_alias_term.pk))
    finally:
        e12_routers.ReadReplicaRouter.enabled = False
    assert response.status_code == 400, response.content[:400]
    assert term_states('default') == before_d, 'default row deleted'
    assert term_states('second') == before_s, 'replica row deleted'


def test_read_replica_detail_put_refused(operator, both_alias_term):
    e12_routers.ReadReplicaRouter.enabled = True
    try:
        before_d = term_states('default')
        before_s = term_states('second')
        response = operator.put(
            TERMS + '{}/'.format(both_alias_term.pk),
            {'name': 'Put changed', 'slug': 'e12-alias-x'}, format='json')
    finally:
        e12_routers.ReadReplicaRouter.enabled = False
    assert response.status_code == 400, response.content[:400]
    assert term_states('default') == before_d
    assert term_states('second') == before_s


def test_read_replica_bulk_post_refused_before_validators(operator):
    import e12_views
    e12_routers.ReadReplicaRouter.enabled = True
    try:
        e12_views.STATE['events'] = []
        with pytest.raises(Exception) as exc_info:
            operator.post(
                '/e12/rec/terms/',
                [{'name': 'Replica refused', 'slug': 'e12-replica-refused'}],
                format='json')
        # Refusal must come either from the EDW one-alias guard or from the
        # provider's own cross-alias guard; both are safe refusals.
        msg = str(exc_info.value).lower()
        assert ('database alias' in msg and ('second' in msg)) or \
               'one database alias' in msg, msg
    finally:
        e12_routers.ReadReplicaRouter.enabled = False
    assert e12_views.STATE['events'] == [], (
        'a state-aware validator ran before the replica refusal: {}'.format(
            e12_views.STATE['events']))
    assert not Term.objects.using('default').filter(slug='e12-replica-refused').exists()
    assert not Term.objects.using('second').filter(slug='e12-replica-refused').exists()


def test_explicit_write_default_router_refuses(operator, both_alias_term):
    e12_routers.ExplicitWriteDefaultRouter.enabled = True
    try:
        before_d = term_states('default')
        before_s = term_states('second')
        response = operator.patch(
            TERMS + '{}/'.format(both_alias_term.pk),
            {'name': 'Changed'}, format='json')
        assert response.status_code == 400, response.content[:400]
        assert term_states('default') == before_d
        assert term_states('second') == before_s

        with pytest.raises(Exception) as exc_info:
            operator.post(
                '/e12/rec/terms/',
                [{'name': 'Explicit bulk', 'slug': 'e12-explicit-bulk'}],
                format='json')
        msg = str(exc_info.value).lower()
        assert 'database alias' in msg, msg
    finally:
        e12_routers.ExplicitWriteDefaultRouter.enabled = False
    assert not Term.objects.using('default').filter(slug='e12-explicit-bulk').exists()
    assert not Term.objects.using('second').filter(slug='e12-explicit-bulk').exists()


def test_instance_hint_write_refused(operator, both_alias_term):
    e12_routers.InstanceHintWriteRouter.enabled = True
    try:
        before_d = term_states('default')
        before_s = term_states('second')
        response = operator.patch(
            TERMS + '{}/'.format(both_alias_term.pk),
            {'name': 'Moved'}, format='json')
    finally:
        e12_routers.InstanceHintWriteRouter.enabled = False
    assert response.status_code == 400, response.content[:400]
    assert term_states('default') == before_d, 'instance hint moved the write to default'
    assert term_states('second') == before_s, 'instance hint moved the write to second'


def test_queryset_bound_view_refused(operator):
    term = Term.objects.using('second').create(name='Bound', slug='e12-bound')
    before_s = term_states('second')
    before_d = term_states('default')
    response = operator.patch(
        '/e12/bound/terms/{}/'.format(term.pk),
        {'name': 'Changed'}, format='json')
    assert response.status_code == 400, response.content[:400]
    assert term_states('second') == before_s
    assert term_states('default') == before_d

    with pytest.raises(Exception) as exc_info:
        operator.post(
            '/e12/bound/terms/',
            [{'name': 'Bound bulk', 'slug': 'e12-bound-bulk'}],
            format='json')
    msg = str(exc_info.value).lower()
    assert 'database alias' in msg, msg
    assert not Term.objects.using('default').filter(slug='e12-bound-bulk').exists()
    assert not Term.objects.using('second').filter(slug='e12-bound-bulk').exists()


# --------------------------------------------------------------------------- #
# R1 / R2 regression controls
# --------------------------------------------------------------------------- #
def test_datamart_declared_scope_deletes_only_that_mart(operator):
    mart_a = DataMart.objects.create(name='Mart A', slug='e12-mart-a')
    mart_b = DataMart.objects.create(name='Mart B', slug='e12-mart-b')
    term_a1 = Term.objects.create(name='A one', slug='e12-a-one')
    term_a2 = Term.objects.create(name='A two', slug='e12-a-two')
    term_b = Term.objects.create(name='B one', slug='e12-b-one')
    mart_a.terms.add(term_a1, term_a2)
    mart_b.terms.add(term_b)
    response = operator.delete(TERMS + '?data_mart_pk={}'.format(mart_a.pk))
    assert response.status_code == 204, response.content[:400]
    assert not Term.objects.filter(pk__in=[term_a1.pk, term_a2.pk]).exists()
    assert Term.objects.filter(pk=term_b.pk).exists(), (
        'a term of another mart was deleted by a named-mart scope')
    assert DataMart.objects.filter(pk__in=[mart_a.pk, mart_b.pk]).count() == 2


def test_nested_children_url_scope_wins_over_body(operator):
    root = Term.objects.create(name='Nested root', slug='e12-nested-root')
    other = Term.objects.create(name='Nested other', slug='e12-nested-other')
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root.pk),
        [{'name': 'URL child', 'slug': 'e12-url-child',
          'parent_id': other.pk}],
        format='json',
    )
    assert response.status_code == 201, response.content[:400]
    child = Term.objects.get(slug='e12-url-child')
    assert child.parent_id == root.pk, 'body parent escaped the URL scope'


def test_nested_children_out_of_scope_target_refused(operator):
    root = Term.objects.create(name='Nested root 2', slug='e12-nested-root2')
    other = Term.objects.create(name='Nested other 2', slug='e12-nested-other2')
    foreign = Term.objects.create(name='Foreign child', slug='e12-foreign-child',
                                  parent=other)
    before = {t.pk: (t.name, t.parent_id) for t in Term.objects.all()}
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root.pk),
        [{'id': foreign.pk, 'name': 'Escaped', 'slug': 'e12-foreign-child'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:400]
    foreign.refresh_from_db()
    assert foreign.name == 'Foreign child'
    assert foreign.parent_id == other.pk


def test_nested_url_conflicting_query_scope_refused(operator):
    root = Term.objects.create(name='Conflict root', slug='e12-conflict-root')
    other = Term.objects.create(name='Conflict other', slug='e12-conflict-other')
    response = operator.get(
        '/edw/api/terms/{}/children/?parent_id={}'.format(root.pk, other.pk))
    assert response.status_code == 400, response.content[:400]
