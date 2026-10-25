# -*- coding: utf-8 -*-
"""
E11/S1: actual Entity / Dynamic RESTMeta write chain on the synthetic model.

The production Entity endpoint is read-only; these tests mount a test-only
writable view (``safety_probe_views.WritableEntityViewSet``) on the existing
materialized ``ContractEntity`` model and exercise the real Dynamic RESTMeta
patching (``create``/``update``/``validate``/``validate_<field>`` hooks,
``permission_classes``) through the whole-batch admission:

* a rejected batch never reaches a RESTMeta hook and never writes;
* the create hook sees a new object state, the update hook sees the admitted
  instance (never a re-resolved one);
* a dynamic ``validate`` hook cannot retarget the admitted identity;
* object permissions for the whole batch are decided before any hook runs;
* ``child.instance`` does not leak between the items of one batch.
"""
from __future__ import unicode_literals

import pytest
from rest_framework.permissions import BasePermission

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import ContractEntity

pytestmark = pytest.mark.django_db

ENTITIES_URL = '/probe/entities/'
TERMS_URL = '/edw/api/terms/'


class DenyEntityPermission(BasePermission):
    """Allow everything except an entity named ``denied``."""

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'name', None) != 'denied'


class RestMetaHarness(object):
    """Recording Dynamic RESTMeta hooks plus mutable hook state.

    The documented RESTMeta hooks are plain functions that receive the child
    serializer as ``self`` after ``DynamicCreateUpdateValidateSerializerMixin``
    patches them, so they are not bound to this object.
    """

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

    def validate_name(self, value):
        harness.events.append(
            ('validate_name', getattr(self, 'instance', None), value))
        return value

    return {
        'create': create,
        'update': update,
        'validate': validate,
        'validate_name': validate_name,
    }


@pytest.fixture
def rest_meta(entity_types):
    meta = ContractEntity._rest_meta
    saved = {
        name: getattr(meta, name, None)
        for name in ('exclude', 'create', 'update', 'validate', 'validate_name',
                     'permission_classes', 'lookup_fields')
    }
    saved_fields = list(getattr(meta, '_fields_validators', []) or [])
    harness = RestMetaHarness()
    hooks = _make_rest_meta_hooks(harness)
    meta.exclude = []
    meta.create = hooks['create']
    meta.update = hooks['update']
    meta.validate = hooks['validate']
    meta.validate_name = hooks['validate_name']
    meta.permission_classes = []
    meta._fields_validators = saved_fields + ['validate_name']
    try:
        yield harness
    finally:
        for name, value in saved.items():
            setattr(meta, name, value)
        meta._fields_validators = saved_fields


def _metas(events, kind):
    return [event for event in events if event[0] == kind]


def test_entity_bulk_create_runs_the_restmeta_create_hook(operator, rest_meta):
    response = operator.post(ENTITIES_URL, [{'name': 'Entity A'}], format='json')
    assert response.status_code == 201, response.content[:600]
    created = ContractEntity.objects.get(name='Entity A')
    creates = _metas(rest_meta.events, 'create')
    assert len(creates) == 1, rest_meta.events
    assert creates[0][1] is None, 'the create hook saw a stale instance'
    assert ContractEntity.objects.filter(pk=created.pk).exists()


def test_entity_bulk_update_binds_the_admitted_instance_to_the_hook(operator, rest_meta):
    first = ContractEntity.objects.create(name='First')
    second = ContractEntity.objects.create(name='Second')
    response = operator.patch(
        ENTITIES_URL,
        [{'id': first.pk, 'name': 'First renamed'},
         {'id': second.pk, 'name': 'Second renamed'}],
        format='json',
    )
    assert response.status_code in (200, 204), response.content[:600]
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == 'First renamed'
    assert second.name == 'Second renamed'
    updates = _metas(rest_meta.events, 'update')
    assert [(event[1].pk, event[1].name) for event in updates] == [
        (first.pk, 'First renamed'), (second.pk, 'Second renamed'),
    ], rest_meta.events


def test_entity_state_is_isolated_between_batch_items(operator, rest_meta):
    first = ContractEntity.objects.create(name='Iso first')
    second = ContractEntity.objects.create(name='Iso second')
    response = operator.patch(
        ENTITIES_URL,
        [{'id': first.pk, 'name': 'Iso first renamed'},
         {'id': second.pk, 'name': 'Iso second renamed'}],
        format='json',
    )
    assert response.status_code in (200, 204), response.content[:600]
    seen = [event[1].pk for event in _metas(rest_meta.events, 'validate') if event[1] is not None]
    assert seen == [first.pk, second.pk], (
        'child.instance leaked between batch items: {}'.format(seen))


def test_entity_dynamic_validator_cannot_retarget_the_admitted_write(operator, rest_meta):
    first = ContractEntity.objects.create(name='Retarget first')
    second = ContractEntity.objects.create(name='Retarget second')
    rest_meta.state['mutate_to'] = second.pk
    response = operator.patch(
        ENTITIES_URL, [{'id': first.pk, 'name': 'Hijacked'}], format='json')
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == 'Retarget first', 'a RESTMeta validator retargeted the write'
    assert second.name == 'Retarget second'
    assert response.status_code == 400, response.content[:600]


def test_entity_dynamic_validator_cannot_retarget_a_create(operator, rest_meta):
    existing = ContractEntity.objects.create(name='Existing target')
    rest_meta.state['mutate_to'] = existing.pk
    response = operator.post(ENTITIES_URL, [{'name': 'New entity'}], format='json')
    existing.refresh_from_db()
    assert existing.name == 'Existing target'
    assert ContractEntity.objects.filter(name='New entity').count() == 0
    assert response.status_code == 400, response.content[:600]


def test_entity_whole_batch_permission_before_any_hook(operator, rest_meta):
    allowed = ContractEntity.objects.create(name='allowed entity')
    denied = ContractEntity.objects.create(name='denied')
    ContractEntity._rest_meta.permission_classes = [DenyEntityPermission]
    response = operator.patch(
        ENTITIES_URL,
        [{'id': allowed.pk, 'name': 'Allowed renamed'},
         {'id': denied.pk, 'name': 'Denied renamed'}],
        format='json',
    )
    allowed.refresh_from_db()
    denied.refresh_from_db()
    assert allowed.name == 'allowed entity'
    assert denied.name == 'denied'
    assert response.status_code in (400, 403), response.content[:600]
    assert rest_meta.events == [], (
        'a RESTMeta hook ran before the whole-batch permission decision: {}'.format(
            rest_meta.events))


def test_entity_unknown_identity_is_refused_before_hooks(operator, rest_meta):
    response = operator.patch(
        ENTITIES_URL, [{'id': 999999, 'name': 'Ghost'}], format='json')
    assert response.status_code == 400, response.content[:600]
    assert rest_meta.events == [], rest_meta.events
    assert not ContractEntity.objects.filter(name='Ghost').exists()


def test_entity_duplicate_target_is_refused_before_hooks(operator, rest_meta):
    entity = ContractEntity.objects.create(name='Duplicate target')
    response = operator.patch(
        ENTITIES_URL,
        [{'id': entity.pk, 'name': 'One'}, {'id': entity.pk, 'name': 'Two'}],
        format='json',
    )
    entity.refresh_from_db()
    assert entity.name == 'Duplicate target'
    assert response.status_code == 400, response.content[:600]
    assert rest_meta.events == [], rest_meta.events


def test_entity_fields_and_nested_mart_scope_stay_intact(operator, rest_meta):
    """The test-only write view does not change the normal read-only default."""
    from edw.views.entity import EntityViewSet

    assert EntityViewSet.permission_classes, 'production entity view lost its permission'
    from edw.rest.permissions import IsReadOnly

    assert EntityViewSet.permission_classes == [IsReadOnly], (
        'the production entity view must stay read-only by default'
    )
