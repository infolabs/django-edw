# -*- coding: utf-8 -*-
"""
E1: контракт Entity, EntityRelation и AdditionalEntityCharacteristicOrMark,
включая выборки subj / rel / subj_and_rel.
"""
from __future__ import unicode_literals

import pytest
from django.db import IntegrityError, transaction

from edw.models.defaults.term import Term
from edw.models.entity import EntityModel
from edw.models.related import (
    AdditionalEntityCharacteristicOrMarkModel,
    EntityRelatedDataMartModel,
)
from edw.tests.contract.app.models import (
    ContractEntity,
    ContractEntityChild,
    DataMart,
    EntityRelation,
)

pytestmark = pytest.mark.django_db


def _entities():
    alpha = ContractEntity.objects.create(name='Alpha')
    beta = ContractEntityChild.objects.create(name='Beta', code='b')
    gamma = ContractEntity.objects.create(name='Gamma')
    return alpha, beta, gamma


def test_polymorphic_manager_returns_real_instances(entity_types):
    alpha, beta, gamma = _entities()
    fetched = {entity.pk: type(entity) for entity in EntityModel.objects.all()}
    assert fetched == {
        alpha.pk: ContractEntity,
        beta.pk: ContractEntityChild,
        gamma.pk: ContractEntity,
    }
    assert EntityModel.objects.get(pk=beta.pk).code == 'b'
    assert ContractEntity.objects.all().count() == 3


def test_entity_type_terms(entity_types):
    alpha, beta, _ = _entities()
    # validate_term_model создаёт корневой термин типа и термин подкласса
    assert entity_types['root'].slug == 'contractentity'
    assert entity_types['child'].slug == 'contractentitychild'
    assert entity_types['child'].parent_id == entity_types['root'].pk
    assert list(alpha.terms.values_list('slug', flat=True)) == ['contractentity']
    assert list(beta.terms.values_list('slug', flat=True)) == ['contractentitychild']


def test_entity_name_and_absolute_url(entity_types):
    alpha = ContractEntity.objects.create(name='Alpha')
    assert alpha.entity_name == 'Alpha'
    assert str(alpha) == 'Alpha'
    assert alpha.get_absolute_url() == '/contractentity/{}/'.format(alpha.pk)
    assert alpha.entity_model == 'contractentity'


def test_entity_relation_str(entity_types):
    alpha, beta, _ = _entities()
    relation_term = Term.objects.create(name='Related', slug='related',
                                        attributes=Term.attributes.is_relation)
    relation = EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)
    assert str(relation) == 'Alpha → Related → Beta'
    assert list(alpha.forward_relations.values_list('pk', flat=True)) == [relation.pk]
    assert list(beta.backward_relations.values_list('pk', flat=True)) == [relation.pk]


def test_entity_relation_unique_together(entity_types):
    alpha, beta, _ = _entities()
    relation_term = Term.objects.create(name='Related', slug='related',
                                        attributes=Term.attributes.is_relation)
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)


def test_subj_forward_and_backward(entity_types):
    alpha, beta, gamma = _entities()
    relation_term = Term.objects.create(name='Related', slug='related',
                                        attributes=Term.attributes.is_relation)
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    names = lambda queryset: sorted(queryset.values_list('name', flat=True))
    assert names(ContractEntity.objects.subj([beta.pk])) == ['Alpha']
    assert names(ContractEntity.objects.subj([alpha.pk])) == ['Beta']
    assert names(ContractEntity.objects.subj([alpha.pk, beta.pk])) == ['Alpha', 'Beta']
    assert names(ContractEntity.objects.subj([gamma.pk])) == []


def test_rel_forward_reverse_and_bidirectional(entity_types):
    alpha, beta, gamma = _entities()
    relation_term = Term.objects.create(name='Related', slug='related',
                                        attributes=Term.attributes.is_relation)
    other_term = Term.objects.create(name='Other', slug='other',
                                     attributes=Term.attributes.is_relation)
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    names = lambda queryset: sorted(queryset.values_list('name', flat=True))
    assert names(ContractEntity.objects.rel([relation_term.pk], [])) == ['Alpha']
    assert names(ContractEntity.objects.rel([], [relation_term.pk])) == ['Beta']
    assert names(ContractEntity.objects.rel([relation_term.pk], [relation_term.pk])) == ['Alpha', 'Beta']
    assert names(ContractEntity.objects.rel([other_term.pk], [])) == []


def test_subj_and_rel_list_and_mapping_modes(entity_types):
    alpha, beta, _ = _entities()
    relation_term = Term.objects.create(name='Related', slug='related',
                                        attributes=Term.attributes.is_relation)
    EntityRelation.objects.create(from_entity=alpha, to_entity=beta, term=relation_term)

    names = lambda queryset: sorted(queryset.values_list('name', flat=True))
    # общий список субъектов
    assert names(ContractEntity.objects.subj_and_rel([beta.pk], [relation_term.pk], [])) == ['Alpha']
    # отдельный список субъектов на связь: непустой список — прямые связи
    assert names(ContractEntity.objects.subj_and_rel({relation_term.pk: [beta.pk]},
                                                     [relation_term.pk], [])) == ['Alpha']
    # пустой список — нет фильтра по субъектам, направление связи сохраняется
    assert names(ContractEntity.objects.subj_and_rel({relation_term.pk: []},
                                                     [relation_term.pk], [])) == ['Alpha']
    # пустой список для обратной связи — сущности на стороне to_entity
    assert names(ContractEntity.objects.subj_and_rel({relation_term.pk: []},
                                                     [], [relation_term.pk])) == ['Beta']


def test_additional_characteristic_or_mark_contract(entity_types):
    alpha, _, _ = _entities()
    characteristic_term = Term.objects.create(name='Color', slug='color',
                                              attributes=Term.attributes.is_characteristic)
    mark_term = Term.objects.create(name='Hot', slug='hot',
                                    attributes=Term.attributes.is_mark)
    characteristic = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        entity=alpha, term=characteristic_term, value='red', view_class='Big RED')
    AdditionalEntityCharacteristicOrMarkModel.objects.create(
        entity=alpha, term=mark_term, value='yes')

    # view_class нормализуется в нижний регистр при save()
    assert characteristic.view_class == 'big red'
    assert str(characteristic) == 'Color: red'

    # additional_characteristics / additional_marks — queryset связей
    assert [(obj.term.slug, obj.value) for obj in alpha.additional_characteristics] == [('color', 'red')]
    assert [(obj.term.slug, obj.value) for obj in alpha.additional_marks] == [('hot', 'yes')]
    # characteristics / marks — уже собранные EntityCharacteristicOrMarkInfo
    assert [(info.name, info.values) for info in alpha.characteristics] == [('Color', ['red'])]
    assert sorted(alpha.additional_characteristics_or_marks.values_list('slug', flat=True)) == ['color', 'hot']


def test_entity_related_data_marts(entity_types):
    alpha, _, _ = _entities()
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    alpha.related_data_marts.add(data_mart)
    assert list(alpha.related_data_marts.values_list('slug', flat=True)) == ['dm']
    assert EntityRelatedDataMartModel.objects.filter(
        entity=alpha, data_mart=data_mart).count() == 1
