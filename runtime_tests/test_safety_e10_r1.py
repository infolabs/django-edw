# -*- coding: utf-8 -*-
"""E11/R1/R2 (ported E10.safetycheck): R1 collection DELETE scope is really applied."""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import DataMart

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'
DATA_MARTS_URL = '/edw/api/data-marts/'


def _term_state():
    return dict(Term.objects.values_list('pk', 'slug'))


def _mart_state():
    return dict(DataMart.objects.values_list('pk', 'slug'))


def _make_leaves(prefix='r1'):
    return [
        Term.objects.create(name='Leaf {}'.format(i), slug='{}-leaf-{}'.format(prefix, i))
        for i in range(3)
    ]


@pytest.mark.parametrize('query', [
    '?slug=does-not-exist',
    '?path=/does-not-exist',
    '?id__in=999999',
    '?unknown_scope=1',
    '?active=true',
    '?semantic_rule=or',
])
def test_undeclared_or_non_scope_parameters_never_delete_terms(operator, query):
    _make_leaves()
    before = _term_state()
    response = operator.delete(TERMS_URL + query)
    after = _term_state()
    assert after == before, 'terms were deleted by non-scope query {}: lost {}'.format(
        query, set(before) - set(after))
    assert response.status_code == 400, (
        'DELETE {} was not refused: {} {}'.format(query, response.status_code,
                                                  response.content[:300]))


def test_empty_and_blank_scope_never_deletes_terms(operator):
    _make_leaves()
    before = _term_state()
    response = operator.delete(TERMS_URL + '?parent_id=&slug=')
    after = _term_state()
    assert after == before
    assert response.status_code == 400, response.content[:300]


def test_declared_parent_scope_deletes_exactly_the_named_children(operator):
    root = Term.objects.create(name='Root', slug='r1-root')
    first = Term.objects.create(name='First', slug='r1-first', parent=root)
    second = Term.objects.create(name='Second', slug='r1-second', parent=root)
    outsider = Term.objects.create(name='Outsider', slug='r1-outsider')
    before = _term_state()
    response = operator.delete(TERMS_URL + '?parent_id={}'.format(root.pk))
    after = _term_state()
    assert response.status_code == 204, response.content[:300]
    assert set(after) == set(before) - {first.pk, second.pk}, (
        'scope parent_id={} did not delete exactly the two children: {}'.format(root.pk, after))
    assert {root.pk, outsider.pk} <= set(after)


def test_declared_scope_plus_unknown_is_refused_without_deletes(operator):
    root = Term.objects.create(name='Root', slug='r1-mix-root')
    Term.objects.create(name='Child', slug='r1-mix-child', parent=root)
    before = _term_state()
    response = operator.delete(TERMS_URL + '?parent_id={}&unknown=1'.format(root.pk))
    after = _term_state()
    assert after == before, 'mixed unknown scope still deleted: {}'.format(set(before) - set(after))
    assert response.status_code == 400, response.content[:300]


@pytest.mark.parametrize('query', [
    '?slug=does-not-exist',
    '?path=/does-not-exist',
    '?id__in=not-a-number',
    '?parent_id=',
])
def test_datamart_scope_must_be_declared_applied_and_valid(operator, query):
    DataMart.objects.create(name='Mart', slug='r1-mart')
    before = _mart_state()
    response = operator.delete(DATA_MARTS_URL + query)
    after = _mart_state()
    assert after == before, 'data marts were deleted by {}: {}'.format(query, set(before) - set(after))
    assert response.status_code == 400, response.content[:300]


def test_datamart_declared_id_scope_deletes_only_that_mart(operator):
    first = DataMart.objects.create(name='First', slug='r1-mart-first')
    second = DataMart.objects.create(name='Second', slug='r1-mart-second')
    outsider = DataMart.objects.create(name='Outsider', slug='r1-mart-outsider')
    before = _mart_state()
    response = operator.delete(DATA_MARTS_URL + '?id__in={}'.format(first.pk))
    after = _mart_state()
    assert response.status_code == 204, response.content[:300]
    assert set(after) == set(before) - {first.pk}
    assert {second.pk, outsider.pk} <= set(after)


def test_datamart_declared_slug_scope_deletes_only_that_mart(operator):
    first = DataMart.objects.create(name='First', slug='r1-slug-first')
    second = DataMart.objects.create(name='Second', slug='r1-slug-second')
    before = _mart_state()
    response = operator.delete(DATA_MARTS_URL + '?slug=r1-slug-first')
    after = _mart_state()
    assert response.status_code == 204, response.content[:300]
    assert set(after) == set(before) - {first.pk}
    assert second.pk in after


def test_declared_but_empty_result_scope_does_not_touch_the_collection(operator):
    root = Term.objects.create(name='Root', slug='r1-empty-root')
    # A child of a non-existent parent is not possible; use a slug scope that
    # the filterset declares (DataMart) and prove an empty result is a no-op.
    DataMart.objects.create(name='Mart', slug='r1-empty-mart')
    before = _mart_state()
    response = operator.delete(DATA_MARTS_URL + '?slug=r1-no-such-slug')
    after = _mart_state()
    assert after == before
    assert response.status_code == 400, response.content[:300]
