# -*- coding: utf-8 -*-
"""
E1: контракт TermModel: дерево MPTT, пути, декомпрессия значений и
семантические правила OR / XOR / AND.
"""
from __future__ import unicode_literals

import pytest
from django.core.exceptions import FieldError
from django.db.models import Q

from edw.models.defaults.term import Term
from edw.models.entity import EntityModel
from edw.models.term import TermModel
from edw.tests.contract.app.models import ContractEntity

pytestmark = pytest.mark.django_db


def test_term_path_ancestors_and_descendants():
    root = Term.objects.create(name='Root', slug='root')
    child = Term.objects.create(name='Child', slug='child', parent=root)
    leaf = Term.objects.create(name='Leaf', slug='leaf', parent=child)

    assert (root.path, child.path, leaf.path) == ('root', 'root/child', 'root/child/leaf')
    assert (root.level, child.level, leaf.level) == (0, 1, 2)
    assert [term.slug for term in leaf.get_ancestors(include_self=True)] == ['root', 'child', 'leaf']
    assert [term.slug for term in root.get_descendants(include_self=True)] == ['root', 'child', 'leaf']
    assert root.is_leaf_node() is False
    assert child.is_leaf_node() is False
    assert leaf.is_leaf_node() is True
    assert list(Term.objects.toplevel().values_list('slug', flat=True)) == ['root']
    assert list(Term.objects.leaf_only().values_list('slug', flat=True)) == ['leaf']


def _legacy_terms():
    """Дерево из backend/edw/tests/test_term.py (эталон декомпрессии)."""
    term1 = Term.objects.create(
        id=1, name='Term1', slug='term1', path='term1', semantic_rule=10,
        attributes='0', specification_mode=10, view_class=None, description='',
        active=True, system_flags='0')
    term2 = Term.objects.create(
        id=2, name='Term2', slug='term2', path='term1/term2', semantic_rule=20,
        attributes='0', specification_mode=10, view_class=None, description='',
        active=True, system_flags='0')
    term2.parent = term1
    term2.save()
    term2_1 = Term.objects.create(
        id=4, name='Term2_1', slug='term2_1', path='term1/term2/term2_1', semantic_rule=10,
        attributes='0', specification_mode=10, view_class=None, description='',
        active=True, system_flags='0')
    term2_1.parent = term2
    term2_1.save()
    term2_2 = Term.objects.create(
        id=5, name='Term2_2', slug='term2_2', path='term1/term2/term2_2', semantic_rule=10,
        attributes='0', specification_mode=10, view_class=None, description='',
        active=True, system_flags='0')
    term2_2.parent = term2
    term2_2.save()
    Term.objects.create(
        id=3, name='Term3', slug='term3', path='term3', semantic_rule=10,
        attributes='0', specification_mode=10, view_class=None, description='',
        active=True, system_flags='0')
    return term1, term2, term2_1, term2_2


def test_term_decompress_contract():
    _legacy_terms()
    assert TermModel.decompress(value=[4, 5]) == {1: [[[], []]], 2: [[], []], 4: [], 5: []}


def test_term_decompress_fix_it_contract():
    _legacy_terms()
    # term2 с правилом XOR и двумя потомками — некорректная ветка, fix_it её схлопывает
    assert TermModel.decompress(value=[4, 5], fix_it=True) == {1: [[]], 2: []}


def test_term_attribute_bit_flags():
    characteristic = Term.attributes.is_characteristic
    mark = Term.attributes.is_mark
    relation = Term.attributes.is_relation
    assert (characteristic, mark, relation) == (1, 2, 4)

    term = Term.objects.create(name='Attr', slug='attr', attributes=characteristic | mark)
    assert term.attributes.is_characteristic is True
    assert term.attributes.is_mark is True
    assert term.attributes.is_relation is False
    # Фильтрация по битовому полю в текущем ядре — точное совпадение маски
    assert Term.objects.filter(attributes=relation).count() == 0
    assert Term.objects.filter(attributes=characteristic).count() == 0
    assert Term.objects.filter(attributes=characteristic | mark).count() == 1


def _semantic_filters(root, children):
    value = [root.pk] + [term.pk for term in children]
    tree = TermModel.decompress(value)
    filters = tree.root.term.make_filters(term_info=tree.root, field_name='terms')
    assert len(filters) == 1
    return filters[0]


def test_semantic_rule_or_filters():
    root = Term.objects.create(name='OR root', slug='or-root', semantic_rule=Term.OR_RULE)
    a = Term.objects.create(name='A', slug='a', parent=root)
    b = Term.objects.create(name='B', slug='b', parent=root)

    query = _semantic_filters(root, [a, b])
    # OR-правило: дизъюнкция точных термов, включая сам корневой термин
    assert query.connector == Q.OR
    assert query.children == [('terms', root.pk), ('terms', a.pk), ('terms', b.pk)]


def test_semantic_rule_xor_behaves_like_or():
    root = Term.objects.create(name='XOR root', slug='xor-root', semantic_rule=Term.XOR_RULE)
    x = Term.objects.create(name='X', slug='x', parent=root)
    y = Term.objects.create(name='Y', slug='y', parent=root)

    query = _semantic_filters(root, [x, y])
    # В текущем ядре XOR обрабатывается ветвью OR (см. BaseTerm.make_filters)
    assert query.connector == Q.OR
    assert query.children == [('terms', root.pk), ('terms', x.pk), ('terms', y.pk)]


def test_semantic_rule_and_filters():
    root = Term.objects.create(name='AND root', slug='and-root', semantic_rule=Term.AND_RULE)
    c = Term.objects.create(name='C', slug='c', parent=root)
    d = Term.objects.create(name='D', slug='d', parent=root)

    query = _semantic_filters(root, [c, d])
    # AND-правило над листовыми потомками сводится к terms__in по активному семейству
    assert query.connector == Q.AND
    assert query.children == [('terms__in', [root.pk, c.pk, d.pk])]


@pytest.mark.xfail(
    reason="semantic_filter() в BaseEntityQuerySet фильтрует через values('entity'), "
           "а автоматическая through-модель называет FK по корневой модели (contractentity)",
    strict=False,
    raises=FieldError,
)
def test_semantic_filter_queryset_contract(entity_types):
    or_root = Term.objects.create(name='OR root', slug='or-root', semantic_rule=Term.OR_RULE)
    a = Term.objects.create(name='A', slug='a', parent=or_root)
    entity = ContractEntity.objects.create(name='A-entity')
    entity.terms.add(a)

    list(EntityModel.objects.semantic_filter([or_root.pk, a.pk]))
