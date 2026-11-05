# -*- coding: utf-8 -*-
"""E12.residualcheck: independent S1 metaclass-cache isolation for Entity."""
from __future__ import unicode_literals

import pytest
from rest_framework.test import APIRequestFactory

from edw.rest.serializers.entity import (
    EntityBulkListSerializer,
    EntityDetailSerializer,
)
from edw.tests.contract.app.models import ContractEntity

pytestmark = pytest.mark.django_db

ENT = '/e12/entities/entities/'


def _warm_entity_list_cache():
    """Instantiate the bare Meta list serializer exactly like a LIST request
    with ?entity_model=... would."""
    request = APIRequestFactory().get(ENT, {'entity_model': 'contractentity'})
    return EntityBulkListSerializer(
        child=EntityDetailSerializer(),
        data=[{'entity_model': 'contractentity'}],
        context={'request': request, 'view': None},
    )


@pytest.fixture
def entity_meta():
    meta = ContractEntity._rest_meta
    saved = {name: getattr(meta, name, None) for name in
             ('create', 'update', 'validate', 'permission_classes', 'exclude',
              'lookup_fields')}
    saved_validators = list(getattr(meta, '_fields_validators', []) or [])
    meta.permission_classes = []
    meta.exclude = []
    meta.lookup_fields = ('id',)
    try:
        yield
    finally:
        for name, value in saved.items():
            setattr(meta, name, value)
        meta._fields_validators = saved_validators


def test_entity_metaclass_cache_is_separate_from_list_meta(
        operator, entity_types, entity_meta):
    _warm_entity_list_cache()
    detail_serializer = EntityDetailSerializer(model=ContractEntity)

    assert isinstance(detail_serializer, EntityDetailSerializer)
    cache = EntityDetailSerializer._meta_cache
    assert cache, 'the dynamic Meta cache was not populated'
    assert all(isinstance(key, tuple) for key in cache), (
        'the dynamic Meta cache is still keyed only by model name: {}'
        .format(sorted(map(repr, cache))))
    list_key = (EntityBulkListSerializer.Meta, 'ContractEntity')
    detail_key = (EntityDetailSerializer.Meta, 'ContractEntity')
    assert list_key in cache, sorted(map(repr, cache))
    assert detail_key in cache, sorted(map(repr, cache))
    assert cache[list_key] is not cache[detail_key], (
        'one serializer class Meta was adopted by the other')
    assert detail_serializer.Meta is cache[detail_key]
    assert detail_serializer.Meta.model is ContractEntity
    assert getattr(detail_serializer.Meta,
                   'need_add_lookup_fields_request_methods', False) is True, (
        'the detail serializer lost its lookup-field request methods')


def test_entity_detail_update_after_list_cache_warm(
        operator, entity_types, entity_meta):
    """The S1 symptom: a detail update after a bare list-Meta cache warm must
    keep its own Meta (lookup-field injection intact)."""
    _warm_entity_list_cache()
    entity = ContractEntity.objects.create(name='E12 warm entity')
    response = operator.patch(
        ENT + '{}/'.format(entity.pk),
        {'name': 'E12 warm entity renamed'}, format='json')
    assert response.status_code in (200, 204), response.content[:600]
    entity.refresh_from_db()
    assert entity.name == 'E12 warm entity renamed'


def test_entity_bulk_upsert_by_id_after_list_cache_warm(
        operator, entity_types, entity_meta):
    _warm_entity_list_cache()
    entity = ContractEntity.objects.create(name='E12 warm bulk entity')
    response = operator.post(
        ENT,
        [{'id': entity.pk, 'name': 'E12 warm bulk renamed'}],
        format='json',
    )
    assert response.status_code in (200, 201), response.content[:600]
    entity.refresh_from_db()
    assert entity.name == 'E12 warm bulk renamed'
    assert ContractEntity.objects.filter(
        name='E12 warm bulk entity').count() == 0
