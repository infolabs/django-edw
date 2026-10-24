# -*- coding: utf-8 -*-
"""
E9/R1: a collection DELETE is bounded only by predicates that were really
applied.

Ports the E8 counter-examples into the product regression gate:

* ``slug`` / ``path`` / ``id__in`` are not declared by ``TermFilter``, so they
  cannot turn "nothing matched" into "delete the whole collection";
* an unknown parameter, an empty scope or a state filter alone never authorizes
  a collection DELETE;
* a declared scope (``parent_id``) deletes only that subtree.

Before/after state is captured before the response status is asserted, so a
wide delete is visible even if the status happens to look right.
"""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import DataMart

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'
DATA_MARTS_URL = '/edw/api/data-marts/'


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


def _make_leaves():
    return [
        Term.objects.create(name='Leaf {}'.format(index), slug='r1-leaf-{}'.format(index))
        for index in range(3)
    ]


def _slugs():
    return sorted(Term.objects.values_list('slug', flat=True))


@pytest.mark.parametrize('query', [
    '?slug=does-not-exist-e9',
    '?path=/does-not-exist-e9',
    '?id__in=999999',
    '?unknown_scope=1',
])
def test_undeclared_or_unknown_scope_cannot_delete_the_collection(operator, query):
    _make_leaves()
    before = _slugs()
    response = operator.delete(TERMS_URL + query)
    after = _slugs()
    assert after == before, 'collection changed by ignored parameter {}'.format(query)
    assert response.status_code == 400, (
        'DELETE {} treated an unapplied parameter as an explicit scope: {}'.format(
            query, response.status_code
        )
    )


def test_empty_scope_cannot_delete_the_collection(operator):
    _make_leaves()
    before = _slugs()
    response = operator.delete(TERMS_URL + '?parent_id=&slug=')
    after = _slugs()
    assert after == before
    assert response.status_code == 400


def test_state_filter_alone_is_not_a_delete_scope(operator):
    _make_leaves()
    before = _slugs()
    response = operator.delete(TERMS_URL + '?active=true')
    after = _slugs()
    assert after == before
    assert response.status_code == 400


def test_declared_parent_scope_deletes_only_that_subtree(operator):
    root = Term.objects.create(name='Root', slug='r1-root')
    first = Term.objects.create(name='First', slug='r1-first', parent=root)
    second = Term.objects.create(name='Second', slug='r1-second', parent=root)
    outsider = Term.objects.create(name='Outsider', slug='r1-outsider')

    response = operator.delete(TERMS_URL + '?parent_id={}'.format(root.pk))
    survivors = set(Term.objects.values_list('pk', flat=True))

    assert response.status_code == 204, response.content[:300]
    assert survivors == {root.pk, outsider.pk}
    assert not {first.pk, second.pk} & survivors


def test_datamart_empty_declared_scope_is_refused(operator):
    DataMart.objects.create(name='Mart', slug='r1-mart')
    before = list(DataMart.objects.values_list('pk', flat=True))
    response = operator.delete(DATA_MARTS_URL + '?slug=does-not-exist-e9')
    after = list(DataMart.objects.values_list('pk', flat=True))
    assert after == before
    assert response.status_code == 400


def test_datamart_invalid_declared_scope_is_refused(operator):
    DataMart.objects.create(name='Mart', slug='r1-invalid-mart')
    before = list(DataMart.objects.values_list('pk', flat=True))
    response = operator.delete(DATA_MARTS_URL + '?id__in=not-a-number')
    after = list(DataMart.objects.values_list('pk', flat=True))
    assert after == before
    assert response.status_code == 400
