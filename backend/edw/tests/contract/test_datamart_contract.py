# -*- coding: utf-8 -*-
"""
E1: контракт DataMart: дерево, активные термины, entities_model,
связи витрины (DataMartRelation) и субъекты связей.
"""
from __future__ import unicode_literals

import pytest
from django.db import IntegrityError, transaction
from django.utils.translation import override

from edw.models.defaults.term import Term
from edw.models.entity import EntityModel
from edw.tests.contract.app.models import (
    ContractEntity,
    ContractEntityChild,
    DataMart,
    DataMartRelation,
)

pytestmark = pytest.mark.django_db


def test_datamart_tree_and_defaults():
    root = DataMart.objects.create(name='Root', slug='root')
    child = DataMart.objects.create(name='Child', slug='child', parent=root)

    assert (root.path, child.path) == ('root', 'root/child')
    assert (root.level, child.level) == (0, 1)
    assert [dm.slug for dm in child.get_ancestors(include_self=True)] == ['root', 'child']
    assert [dm.slug for dm in root.get_descendants(include_self=True)] == ['root', 'child']
    assert list(DataMart.objects.toplevel().values_list('slug', flat=True)) == ['root']

    assert root.ordering == '-created_at'
    assert root.view_component == 'list'
    assert root.limit is None
    assert root.active is True
    assert root.get_absolute_url() == '/datamart/{}/'.format(root.pk)
    assert str(root) == 'Root'


def test_datamart_third_level_insertion():
    root = DataMart.objects.create(name='Root', slug='root')
    child = DataMart.objects.create(name='Child', slug='child', parent=root)
    DataMart.objects.create(name='Leaf', slug='leaf', parent=child)


def test_datamart_active_terms_ids():
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    active_term = Term.objects.create(name='Active', slug='active')
    inactive_term = Term.objects.create(name='Inactive', slug='inactive', active=False)
    data_mart.terms.set([active_term, inactive_term])

    fresh = DataMart.objects.get(pk=data_mart.pk)
    assert fresh.active_terms_ids == [active_term.pk]


def test_datamart_entities_model_without_type_terms():
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    assert data_mart.entities_model is ContractEntity
    assert data_mart.entities_model is EntityModel.materialized


def test_datamart_entities_model_by_type_term(entity_types):
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    data_mart.terms.add(entity_types['child'])
    fresh = DataMart.objects.get(pk=data_mart.pk)
    assert fresh.active_terms_ids == [entity_types['child'].pk]
    assert fresh.entities_model is ContractEntityChild

    data_mart.terms.set([entity_types['root']])
    fresh = DataMart.objects.get(pk=data_mart.pk)
    assert fresh.entities_model is ContractEntity


def test_datamart_entities_model_unrelated_term(entity_types):
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    unrelated = Term.objects.create(name='Unrelated', slug='unrelated')
    data_mart.terms.add(unrelated)
    fresh = DataMart.objects.get(pk=data_mart.pk)
    assert fresh.entities_model is ContractEntity


def test_datamart_relation_defaults_and_str():
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    relation_term = Term.objects.create(name='Related', slug='related')
    relation = DataMartRelation.objects.create(data_mart=data_mart, term=relation_term)

    assert relation.direction == DataMartRelation.RELATION_BIDIRECTIONAL == 'b'
    with override('en'):
        assert str(relation) == 'DM `{}{}` ← Bidirectional: Related'.format(relation.pk, 'b')


def test_datamart_relation_unique_together():
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    relation_term = Term.objects.create(name='Related', slug='related')
    DataMartRelation.objects.create(data_mart=data_mart, term=relation_term, direction='f')
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            DataMartRelation.objects.create(data_mart=data_mart, term=relation_term, direction='r')


def test_datamart_is_subjective_and_relations_subjects(entity_types):
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    subject = ContractEntity.objects.create(name='Subject')
    forward_term = Term.objects.create(name='Forward', slug='forward')
    reverse_term = Term.objects.create(name='Reverse', slug='reverse')

    assert data_mart.is_subjective is False

    forward = DataMartRelation.objects.create(data_mart=data_mart, term=forward_term, direction='f')
    reverse = DataMartRelation.objects.create(data_mart=data_mart, term=reverse_term, direction='r')
    forward.subjects.add(subject)

    fresh = DataMart.objects.get(pk=data_mart.pk)
    relations = list(fresh.relations.all())
    assert fresh.is_subjective is True
    # ключи словаря — term_id связей (не id самих DataMartRelation)
    assert DataMart.get_relations_subjects(relations) == {
        forward_term.pk: [subject.pk],
        reverse_term.pk: [],
    }
    assert DataMart.separate_relations(relations) == ([forward_term.pk], [reverse_term.pk])


def test_datamart_relation_separate_directions():
    data_mart = DataMart.objects.create(name='DM', slug='dm')
    bidirectional_term = Term.objects.create(name='B', slug='b')
    forward_term = Term.objects.create(name='F', slug='f')
    reverse_term = Term.objects.create(name='R', slug='r')
    bidirectional = DataMartRelation.objects.create(data_mart=data_mart, term=bidirectional_term)
    forward = DataMartRelation.objects.create(data_mart=data_mart, term=forward_term, direction='f')
    reverse = DataMartRelation.objects.create(data_mart=data_mart, term=reverse_term, direction='r')

    # separate_relations возвращает term_id связей, а не id DataMartRelation
    forward_ids, reverse_ids = DataMart.separate_relations(
        [bidirectional, forward, reverse])
    assert forward_ids == [bidirectional_term.pk, forward_term.pk]
    assert reverse_ids == [bidirectional_term.pk, reverse_term.pk]
