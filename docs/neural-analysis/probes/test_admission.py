# -*- coding: utf-8 -*-
"""E12.residualcheck: independent S1/R3 two-stage admission controls."""
from __future__ import unicode_literals

import pytest
from rest_framework.permissions import BasePermission

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import ContractEntity, DataMart

import e12_views

pytestmark = pytest.mark.django_db

TERMS = '/edw/api/terms/'
REC = '/e12/rec/terms/'
HOOK = '/e12/hook/terms/'
MUT = '/e12/mutate/terms/'
PERM = '/e12/permission/terms/'
ENT = '/e12/entities/entities/'


def term_rows(alias='default'):
    return {
        term.pk: (term.name, term.slug, term.parent_id)
        for term in Term.objects.using(alias).all()
    }


@pytest.fixture
def scope(db):
    root = Term.objects.create(name='Root', slug='e12-root')
    other = Term.objects.create(name='Other', slug='e12-other')
    target = Term.objects.create(name='Target', slug='e12-target', parent=other)
    inside = Term.objects.create(name='Inside', slug='e12-inside', parent=root)
    return root, other, target, inside


def _events():
    return list(e12_views.STATE['events'])


def test_field_hook_does_not_run_for_forbidden_id(operator, scope):
    root, other, target, inside = scope
    before = term_rows()
    response = operator.post(
        HOOK + '?parent_id={}'.format(root.pk),
        [{'id': target.pk, 'name': 'Escaped', 'slug': 'e12-target'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:400]
    assert term_rows() == before, 'a refused batch changed the database'
    assert _events() == [], (
        'a state-aware field hook ran before whole-batch admission: {}'.format(_events()))


def test_field_hook_does_not_run_for_foreign_natural_key(operator, scope):
    root, other, target, inside = scope
    before = term_rows()
    response = operator.post(
        HOOK + '?parent_id={}'.format(root.pk),
        [{'name': 'Shadow', 'slug': 'e12-target'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:400]
    assert term_rows() == before
    assert _events() == [], _events()


def test_whole_batch_permission_is_decided_before_any_validator(operator, scope):
    root, other, target, inside = scope
    denied = Term.objects.create(name='Denied', slug='e12-denied', parent=root)
    e12_views.STATE['deny_slugs'] = {'e12-denied'}
    before = term_rows()
    response = operator.patch(
        PERM + '?parent_id={}'.format(root.pk),
        [{'id': inside.pk, 'name': 'Interleaved'},
         {'id': denied.pk, 'name': 'Denied update'}],
        format='json',
    )
    assert response.status_code in (400, 403), response.content[:400]
    assert term_rows() == before, 'a refused batch wrote rows'
    events = _events()
    validator_events = [e for e in events if e[0] in ('run_validation', 'validate')]
    assert validator_events == [], (
        'validators ran before the whole-batch permission decision: {}'.format(events))
    perm_pks = {e[1] for e in events if e[0] == 'obj_perm'}
    assert perm_pks == {inside.pk, denied.pk}, (
        'both batch items were not authorized before validation: {}'.format(events))


def test_validator_cannot_retarget_an_admitted_update(operator, scope):
    root, other, target, inside = scope
    e12_views.STATE['mutate_field'] = 'id'
    e12_views.STATE['mutate_to'] = target.pk
    before = term_rows()
    response = operator.patch(
        MUT + '?parent_id={}'.format(root.pk),
        [{'id': inside.pk, 'name': 'Hijacked'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:400]
    assert term_rows() == before, 'the mutated identity was written'


def test_validator_cannot_retarget_an_admitted_create(operator, scope):
    root, other, target, inside = scope
    e12_views.STATE['mutate_field'] = 'slug'
    e12_views.STATE['mutate_to'] = 'e12-inside'
    before = term_rows()
    response = operator.post(
        MUT + '?parent_id={}'.format(root.pk),
        [{'name': 'Mutation', 'slug': 'e12-new-slug'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:400]
    assert term_rows() == before, 'the retargeted create was written'
    assert not Term.objects.filter(slug='e12-new-slug').exists()


def test_upsert_by_in_scope_id_updates_the_admitted_target(operator, scope):
    root, other, target, inside = scope
    response = operator.post(
        REC + '?parent_id={}'.format(root.pk),
        [{'id': inside.pk, 'name': 'Renamed inside', 'slug': 'e12-inside'}],
        format='json',
    )
    assert response.status_code in (200, 201), response.content[:400]
    inside.refresh_from_db()
    assert inside.name == 'Renamed inside'
    assert inside.slug == 'e12-inside'


def test_new_natural_key_can_create(operator, scope):
    request_ids = set(Term.objects.values_list('pk', flat=True))
    response = operator.post(
        REC, [{'name': 'Brand new', 'slug': 'e12-brand-new'}], format='json')
    assert response.status_code == 201, response.content[:400]
    created = Term.objects.get(slug='e12-brand-new')
    assert created.pk not in request_ids


@pytest.mark.parametrize('payload_kind', ['unknown_id', 'duplicate', 'ambiguous',
                                          'out_of_scope'])
def test_identity_refusals_leave_no_writes(operator, scope, payload_kind):
    root, other, target, inside = scope
    second_inside = Term.objects.create(
        name='Second inside', slug='e12-second-inside', parent=root)
    before = term_rows()
    if payload_kind == 'unknown_id':
        payload = [{'id': 999999, 'name': 'Ghost', 'slug': 'e12-ghost'}]
    elif payload_kind == 'duplicate':
        payload = [{'id': inside.pk, 'name': 'One'},
                   {'id': inside.pk, 'name': 'Two'}]
    elif payload_kind == 'ambiguous':
        payload = [{'id': inside.pk, 'name': 'Ambiguous',
                    'slug': 'e12-second-inside'}]
    else:
        payload = [{'id': target.pk, 'name': 'Escaped', 'slug': 'e12-target'}]
    response = operator.post(
        REC + '?parent_id={}'.format(root.pk), payload, format='json')
    assert response.status_code == 400, response.content[:400]
    assert term_rows() == before, '{} produced writes'.format(payload_kind)
    assert not Term.objects.filter(slug='e12-ghost').exists()
    assert second_inside.name == 'Second inside'


def test_child_instance_does_not_leak_between_batch_items(operator):
    first = Term.objects.create(name='Iso first', slug='e12-iso-first')
    second = Term.objects.create(name='Iso second', slug='e12-iso-second')
    response = operator.patch(
        REC,
        [{'id': first.pk, 'name': 'Iso first renamed'},
         {'id': second.pk, 'name': 'Iso second renamed'}],
        format='json',
    )
    assert response.status_code in (200, 201), response.content[:400]
    seen = [event[1] for event in _events() if event[0] == 'validate']
    assert seen == [first.pk, second.pk], (
        'child.instance leaked between items: {}'.format(seen))


# --------------------------------------------------------------------------- #
# Real Dynamic RESTMeta hooks for the Entity chain
# --------------------------------------------------------------------------- #
class RecordingDenyNamePermission(BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        STATE.append(('obj_perm', getattr(obj, 'pk', None), getattr(obj, 'name', None)))
        return getattr(obj, 'name', None) != 'denied'


STATE = []


def _hook(fn_name):
    def create(self, validated_data):
        STATE.append(('create', getattr(self, 'instance', None), dict(validated_data)))
        return super(type(self), self).create(validated_data)

    def update(self, instance, validated_data):
        STATE.append(('update', instance, dict(validated_data)))
        return super(type(self), self).update(instance, validated_data)

    def validate(self, attrs):
        STATE.append(('validate', getattr(self, 'instance', None), None))
        if HOOK_STATE.get('mutate_to') is not None:
            attrs = dict(attrs)
            attrs['id'] = HOOK_STATE['mutate_to']
        return attrs

    return {'create': create, 'update': update, 'validate': validate}[fn_name]


HOOK_STATE = {'mutate_to': None}


@pytest.fixture
def entity_meta():
    meta = ContractEntity._rest_meta
    saved = {name: getattr(meta, name, None) for name in
             ('create', 'update', 'validate', 'permission_classes', 'exclude',
              'lookup_fields')}
    saved_validators = list(getattr(meta, '_fields_validators', []) or [])
    STATE[:] = []
    HOOK_STATE['mutate_to'] = None
    meta.create = _hook('create')
    meta.update = _hook('update')
    meta.validate = _hook('validate')
    meta.permission_classes = []
    meta.exclude = []
    meta.lookup_fields = ('id',)
    try:
        yield STATE
    finally:
        for name, value in saved.items():
            setattr(meta, name, value)
        meta._fields_validators = saved_validators
        HOOK_STATE['mutate_to'] = None


def test_entity_restmeta_create_hook_sees_new_state(operator, entity_types, entity_meta):
    response = operator.post(ENT, [{'name': 'E12 entity A'}], format='json')
    assert response.status_code == 201, response.content[:400]
    created = ContractEntity.objects.get(name='E12 entity A')
    creates = [event for event in entity_meta if event[0] == 'create']
    assert len(creates) == 1 and creates[0][1] is None, entity_meta
    assert ContractEntity.objects.filter(pk=created.pk).exists()


def test_entity_restmeta_update_binds_the_admitted_instance(
        operator, entity_types, entity_meta):
    first = ContractEntity.objects.create(name='E12 first')
    second = ContractEntity.objects.create(name='E12 second')
    response = operator.patch(
        ENT,
        [{'id': first.pk, 'name': 'E12 first renamed'},
         {'id': second.pk, 'name': 'E12 second renamed'}],
        format='json',
    )
    assert response.status_code in (200, 201), response.content[:400]
    updates = [event[1].pk for event in entity_meta if event[0] == 'update']
    validates = [event[1].pk for event in entity_meta if event[0] == 'validate']
    assert updates == [first.pk, second.pk], entity_meta
    assert validates == [first.pk, second.pk], (
        'validate hook did not see the admitted instance in item order: {}'.format(
            entity_meta))
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == 'E12 first renamed' and second.name == 'E12 second renamed'


def test_entity_restmeta_validator_cannot_retarget(operator, entity_types, entity_meta):
    first = ContractEntity.objects.create(name='E12 fixed first')
    second = ContractEntity.objects.create(name='E12 fixed second')
    HOOK_STATE['mutate_to'] = second.pk
    response = operator.patch(
        ENT, [{'id': first.pk, 'name': 'Hijacked'}], format='json')
    assert response.status_code == 400, response.content[:400]
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.name == 'E12 fixed first'
    assert second.name == 'E12 fixed second'


def test_entity_whole_batch_permission_before_any_hook(
        operator, entity_types, entity_meta):
    allowed = ContractEntity.objects.create(name='allowed entity')
    denied = ContractEntity.objects.create(name='denied')
    ContractEntity._rest_meta.permission_classes = [RecordingDenyNamePermission]
    response = operator.patch(
        ENT,
        [{'id': allowed.pk, 'name': 'allowed renamed'},
         {'id': denied.pk, 'name': 'denied renamed'}],
        format='json',
    )
    assert response.status_code in (400, 403), response.content[:400]
    hooks = [event for event in entity_meta if event[0] in ('create', 'update', 'validate')]
    assert hooks == [], 'a RESTMeta hook ran before the batch permission: {}'.format(hooks)
    checked = {event[1] for event in entity_meta if event[0] == 'obj_perm'}
    assert checked == {allowed.pk, denied.pk}, (
        'not every batch item was authorized before validation: {}'.format(entity_meta))
    allowed.refresh_from_db()
    denied.refresh_from_db()
    assert allowed.name == 'allowed entity' and denied.name == 'denied'


# --------------------------------------------------------------------------- #
# Real Dynamic RESTMeta hooks for the DataMart chain + metaclass cache
# --------------------------------------------------------------------------- #
@pytest.fixture
def datamart_meta():
    meta = DataMart._rest_meta
    saved = {name: getattr(meta, name, None) for name in
             ('create', 'update', 'validate', 'permission_classes', 'exclude')}
    saved_validators = list(getattr(meta, '_fields_validators', []) or [])
    STATE[:] = []
    HOOK_STATE['mutate_to'] = None

    def create(self, validated_data):
        STATE.append(('create', getattr(self, 'instance', None), dict(validated_data)))
        return super(type(self), self).create(validated_data)

    def update(self, instance, validated_data):
        STATE.append(('update', instance, dict(validated_data)))
        return super(type(self), self).update(instance, validated_data)

    def validate(self, attrs):
        STATE.append(('validate', getattr(self, 'instance', None), None))
        return attrs

    meta.create = create
    meta.update = update
    meta.validate = validate
    meta.permission_classes = []
    meta.exclude = []
    try:
        yield STATE
    finally:
        for name, value in saved.items():
            setattr(meta, name, value)
        meta._fields_validators = saved_validators


def test_datamart_restmeta_create_and_update_hooks(operator, datamart_meta):
    existing = DataMart.objects.create(name='E12 existing mart', slug='e12-existing-mart')
    response = operator.post(
        '/edw/api/data-marts/',
        [{'name': 'E12 new mart', 'slug': 'e12-new-mart'},
         {'id': existing.pk, 'name': 'E12 existing renamed',
          'slug': 'e12-existing-mart'}],
        format='json',
    )
    assert response.status_code == 201, response.content[:600]
    existing.refresh_from_db()
    assert existing.name == 'E12 existing renamed'
    assert DataMart.objects.filter(slug='e12-new-mart').count() == 1
    creates = [event for event in datamart_meta if event[0] == 'create']
    updates = [event for event in datamart_meta if event[0] == 'update']
    assert len(creates) == 1 and creates[0][1] is None, datamart_meta
    assert len(updates) == 1 and updates[0][1].pk == existing.pk, datamart_meta


def test_datamart_metaclass_cache_is_separate(operator):
    from edw.rest.serializers.data_mart import (
        DataMartBulkListSerializer, DataMartDetailSerializer)

    # Warm the cache exactly like a preceding bare list-serializer use did.
    list_serializer = DataMartDetailSerializer(many=True)
    detail_serializer = DataMartDetailSerializer()
    assert isinstance(list_serializer, DataMartBulkListSerializer)
    assert detail_serializer.Meta is not list_serializer.Meta, (
        'the list serializer Meta was adopted by the detail serializer')
    assert getattr(detail_serializer.Meta,
                   'need_add_lookup_fields_request_methods', False) is True, (
        'the detail serializer lost its lookup-field request methods')
    model = getattr(detail_serializer.Meta, 'model', None)
    assert model is not None
    assert all(isinstance(key, tuple) for key in DataMartDetailSerializer._meta_cache), (
        'the dynamic Meta cache is still keyed only by model name')

    # The regression symptom: a POST upsert by the admitted id must still work.
    existing = DataMart.objects.create(name='E12 cache existing',
                                       slug='e12-cache-existing')
    response = operator.post(
        '/edw/api/data-marts/',
        [{'id': existing.pk, 'name': 'E12 cache renamed',
          'slug': 'e12-cache-existing'}],
        format='json',
    )
    assert response.status_code in (200, 201), response.content[:600]
    existing.refresh_from_db()
    assert existing.name == 'E12 cache renamed'
