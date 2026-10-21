# -*- coding: utf-8 -*-
"""
E3: регрессии SQL-слоя EDW.

* CustomJoin и JOIN из «сырого» подзапроса (контракт Django 4.2/5.2);
* custom GROUP BY (patches/sql/compiler.py);
* направление и ключ кэша выборок subj / rel / subj_and_rel.
"""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import ContractEntity, EntityRelation

pytestmark = pytest.mark.django_db


def _entities():
    return [
        ContractEntity.objects.create(name=name)
        for name in ('Alpha', 'Beta', 'Gamma')
    ]


def _relation_term(slug='related', name='Related'):
    return Term.objects.create(name=name, slug=slug,
                               attributes=Term.attributes.is_relation)


def _names(queryset):
    return sorted(queryset.values_list('name', flat=True))


# ==============================================================================
# CustomJoin / JOIN из подзапроса
# ==============================================================================

def test_group_by_produces_group_by_sql(entity_types):
    _entities()

    queryset = ContractEntity.objects.all().group_by('name')
    sql = str(queryset.query)

    assert 'GROUP BY' in sql.upper()
    assert ' GROUP_SIZE' not in sql  # extra-поле не попадает в GROUP BY
    assert sorted(queryset.values_list('name', flat=True)) == ['Alpha', 'Beta', 'Gamma']
    assert queryset.count() == 3


def test_group_by_aggregates_same_values(entity_types):
    alpha, beta, gamma = _entities()
    ContractEntity.objects.filter(pk__in=[alpha.pk, beta.pk]).update(name='Same')

    queryset = ContractEntity.objects.all().group_by('name')
    rows = list(queryset.values_list('name', 'group_size').order_by('name'))
    assert rows == [('Gamma', 1), ('Same', 2)]


def test_inner_join_with_raw_subquery(entity_types):
    alpha, beta, gamma = _entities()
    inner_qs = ContractEntity.objects.raw(str(
        ContractEntity.objects.filter(pk__in=[alpha.pk, gamma.pk]).values('id').query
    ))
    joined = ContractEntity.objects.inner_join(inner_qs, 'id', 'id', 'joined_entities')
    assert _names(joined) == ['Alpha', 'Gamma']


def test_left_join_with_raw_subquery(entity_types):
    alpha, beta, gamma = _entities()
    inner_qs = ContractEntity.objects.raw(str(
        ContractEntity.objects.filter(pk=alpha.pk).values('id').query
    ))
    joined = ContractEntity.objects.left_join(inner_qs, 'id', 'id', 'joined_entities')
    assert _names(joined) == ['Alpha', 'Beta', 'Gamma']


# ==============================================================================
# subj / rel / subj_and_rel: направление связей
# ==============================================================================

def test_subj_and_rel_empty_subject_list_keeps_direction(entity_types):
    alpha, beta, _ = _entities()
    relation_term = _relation_term()
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    # нет субъектов, прямая связь: сущности на стороне from_entity (как в rel())
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: []}, [relation_term.pk], [])) == ['Alpha']
    # нет субъектов, обратная связь: сущности на стороне to_entity (как в rel())
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: []}, [], [relation_term.pk])) == ['Beta']
    # обе стороны
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: []}, [relation_term.pk], [relation_term.pk])) == ['Alpha', 'Beta']
    # эквивалентность rel() по тому же терму без субъектов
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: []}, [relation_term.pk], [])) == _names(
        ContractEntity.objects.rel([relation_term.pk], []))


def test_subj_and_rel_non_empty_subject_list_keeps_direction(entity_types):
    alpha, beta, _ = _entities()
    relation_term = _relation_term()
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    # прямая связь с субъектом: сущности, связанные с субъектом beta
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: [beta.pk]}, [relation_term.pk], [])) == ['Alpha']
    # обратная связь с субъектом: сущности, с которыми связан субъект alpha
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: [alpha.pk]}, [], [relation_term.pk])) == ['Beta']
    # чужой субъект не даёт совпадений
    assert _names(ContractEntity.objects.subj_and_rel(
        {relation_term.pk: [alpha.pk]}, [relation_term.pk], [])) == []


# ==============================================================================
# subj / rel / subj_and_rel: ключ кэша
# ==============================================================================

def test_subj_and_rel_cache_key_is_plain_string(entity_types):
    alpha, beta, _ = _entities()
    relation_term = _relation_term()
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    subj_ids = [beta.pk]
    rel_f_ids = [relation_term.pk]
    queryset = ContractEntity.objects.subj_and_rel(subj_ids, rel_f_ids, [])
    base = ContractEntity.objects.all()

    # висячая запятая в _get_subj_and_rel_cache_key превращала ключ в кортеж
    cache_key = base._get_subj_and_rel_cache_key(subj_ids, rel_f_ids, [])
    assert isinstance(cache_key, str)
    assert cache_key == '{}:{}'.format(
        base._get_subj_cache_key(subj_ids), base._get_rel_cache_key(rel_f_ids, []))
    assert not cache_key.startswith('(')
    assert isinstance(queryset._cache_key, str)
    assert '(' not in queryset._cache_key

    mapping_queryset = ContractEntity.objects.subj_and_rel({relation_term.pk: subj_ids}, rel_f_ids, [])
    mapping_key = base._get_subj_and_rel_cache_key({relation_term.pk: subj_ids}, rel_f_ids, [])
    assert isinstance(mapping_key, str)
    assert not mapping_key.startswith('(')
    assert ':rel:' in mapping_key
    assert isinstance(mapping_queryset._cache_key, str)


def test_subj_and_rel_cache_keys_differ_by_mode_and_direction(entity_types):
    alpha, beta, _ = _entities()
    relation_term = _relation_term()
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    list_key = ContractEntity.objects.subj_and_rel([beta.pk], [relation_term.pk], [])._cache_key
    mapping_key = ContractEntity.objects.subj_and_rel(
        {relation_term.pk: [beta.pk]}, [relation_term.pk], [])._cache_key
    reverse_key = ContractEntity.objects.subj_and_rel(
        {relation_term.pk: [beta.pk]}, [], [relation_term.pk])._cache_key

    # разные выборки не должны переиспользовать чужой ключ кэша
    assert len({list_key, mapping_key, reverse_key}) == 3
    # ключи стабильны между вызовами
    assert list_key == ContractEntity.objects.subj_and_rel([beta.pk], [relation_term.pk], [])._cache_key
