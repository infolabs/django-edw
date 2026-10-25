# -*- coding: utf-8 -*-
"""
E11/S1: DataMart whole-batch admission and its actual RESTMeta write chain.

The data-mart list serializer is a second consumer of
``ScopedBulkAdmissionMixin`` with its own ``DataMartDynamicMetaMixin``.  These
tests cover the same invariants as the Term/Entity suites on that path: typed
identity, scoped target and whole-batch permissions before any state-aware
hook, an immutable admitted identity, and the real Dynamic RESTMeta
``create``/``update``/``validate`` hooks.
"""
from __future__ import unicode_literals

import pytest

from edw.tests.contract.app.models import DataMart

pytestmark = pytest.mark.django_db

DATA_MARTS_URL = '/edw/api/data-marts/'
PERMISSION_MARTS_URL = '/probe/data-marts/'


class RestMetaHarness(object):
    def __init__(self):
        self.events = []
        self.state = {'mutate_to': None}


def _make_rest_meta_hooks(harness):
    def create(self, validated_data):
        harness.events.append(
            ('create', getattr(self, 'instance', None), dict(validated_data)))
        return super(type(self), self).create(validated_data)

    def update(self, instance, validated_data):
        harness.events.append(('update', instance, dict(validated_data)))
        return super(type(self), self).update(instance, validated_data)

    def validate(self, attrs):
        harness.events.append(('validate', getattr(self, 'instance', None), None))
        if harness.state['mutate_to'] is not None:
            attrs = dict(attrs)
            attrs['id'] = harness.state['mutate_to']
        return attrs

    return {'create': create, 'update': update, 'validate': validate}


@pytest.fixture
def rest_meta():
    meta = DataMart._rest_meta
    saved = {
        name: getattr(meta, name, None)
        for name in ('exclude', 'create', 'update', 'validate', 'permission_classes',
                     'lookup_fields')
    }
    harness = RestMetaHarness()
    hooks = _make_rest_meta_hooks(harness)
    meta.exclude = []
    meta.create = hooks['create']
    meta.update = hooks['update']
    meta.validate = hooks['validate']
    meta.permission_classes = []
    try:
        yield harness
    finally:
        for name, value in saved.items():
            setattr(meta, name, value)


def test_datamart_bulk_post_creates_and_upserts_inside_scope(operator, rest_meta):
    existing = DataMart.objects.create(name='Existing mart', slug='s1-existing-mart')
    response = operator.post(
        DATA_MARTS_URL,
        [{'name': 'New mart', 'slug': 's1-new-mart'},
         {'id': existing.pk, 'name': 'Existing renamed', 'slug': 's1-existing-mart'}],
        format='json',
    )
    assert response.status_code == 201, response.content[:600]
    created = DataMart.objects.get(slug='s1-new-mart')
    existing.refresh_from_db()
    assert existing.name == 'Existing renamed'
    assert DataMart.objects.filter(pk=created.pk).exists()
    creates = [event for event in rest_meta.events if event[0] == 'create']
    updates = [event for event in rest_meta.events if event[0] == 'update']
    assert len(creates) == 1 and creates[0][1] is None, rest_meta.events
    assert len(updates) == 1 and updates[0][1].pk == existing.pk, rest_meta.events


def test_datamart_unknown_identity_is_refused_before_hooks(operator, rest_meta):
    response = operator.post(
        DATA_MARTS_URL, [{'id': 999999, 'name': 'Ghost', 'slug': 's1-ghost'}],
        format='json')
    assert not DataMart.objects.filter(slug='s1-ghost').exists()
    assert response.status_code == 400, response.content[:600]
    assert rest_meta.events == [], rest_meta.events


def test_datamart_duplicate_target_is_refused_before_hooks(operator, rest_meta):
    mart = DataMart.objects.create(name='Duplicate mart', slug='s1-duplicate')
    response = operator.post(
        DATA_MARTS_URL,
        [{'id': mart.pk, 'name': 'One', 'slug': 's1-duplicate'},
         {'id': mart.pk, 'name': 'Two', 'slug': 's1-duplicate'}],
        format='json',
    )
    mart.refresh_from_db()
    assert mart.name == 'Duplicate mart'
    assert response.status_code == 400, response.content[:600]
    assert rest_meta.events == [], rest_meta.events


def test_datamart_dynamic_validator_cannot_retarget_the_admitted_write(operator, rest_meta):
    first = DataMart.objects.create(name='First mart', slug='s1-first')
    second = DataMart.objects.create(name='Second mart', slug='s1-second')
    rest_meta.state['mutate_to'] = second.pk
    response = operator.patch(
        DATA_MARTS_URL, [{'id': first.pk, 'name': 'Hijacked'}], format='json')
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == 'First mart', 'a DataMart RESTMeta validator retargeted the write'
    assert second.name == 'Second mart'
    assert response.status_code == 400, response.content[:600]


def test_datamart_whole_batch_permission_before_any_hook(operator, rest_meta):
    allowed = DataMart.objects.create(name='Allowed mart', slug='allowed-mart')
    denied = DataMart.objects.create(name='Denied mart', slug='denied-mart')
    response = operator.patch(
        PERMISSION_MARTS_URL,
        [{'id': allowed.pk, 'name': 'Allowed renamed'},
         {'id': denied.pk, 'name': 'Denied renamed'}],
        format='json',
    )
    allowed.refresh_from_db()
    denied.refresh_from_db()
    assert allowed.name == 'Allowed mart' and denied.name == 'Denied mart'
    assert response.status_code in (400, 403), response.content[:600]
    assert rest_meta.events == [], (
        'a DataMart RESTMeta hook ran before the whole-batch permission decision: '
        '{}'.format(rest_meta.events))


def test_datamart_nested_url_parent_is_the_admitted_scope(operator, rest_meta):
    parent = DataMart.objects.create(name='Parent mart', slug='s1-parent')
    other = DataMart.objects.create(name='Other mart', slug='s1-other')
    foreign_child = DataMart.objects.create(
        name='Foreign child', slug='s1-foreign-child', parent=other)
    response = operator.post(
        '/edw/api/data-marts/{}/children/'.format(parent.pk),
        [{'id': foreign_child.pk, 'name': 'Escaped', 'slug': 's1-foreign-child'}],
        format='json',
    )
    foreign_child.refresh_from_db()
    assert foreign_child.name == 'Foreign child'
    assert response.status_code == 400, response.content[:600]

    response = operator.post(
        '/edw/api/data-marts/{}/children/'.format(parent.pk),
        [{'name': 'URL child', 'slug': 's1-url-child', 'parent_id': other.pk}],
        format='json',
    )
    assert response.status_code == 201, response.content[:600]
    child = DataMart.objects.get(slug='s1-url-child')
    assert child.parent_id == parent.pk, (
        'the body parent_id escaped the nested URL parent: {}'.format(child.parent_id))
