# -*- coding: utf-8 -*-
"""
E9/R2: the nested URL parent is mandatory for every write method.

Ports the E8 counter-examples into the product regression gate:

* a query-string ``parent_id`` cannot replace the URL parent;
* a body ``parent_id`` / ``parent__slug`` cannot re-point a create outside the
  URL parent (the URL value wins and is the saved identity);
* a nested children collection DELETE is bounded by the URL parent;
* a nested data-mart collection scopes POST and DELETE to that data mart.
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


@pytest.fixture
def two_roots():
    root_a = Term.objects.create(name='Root A', slug='r2-root-a')
    root_b = Term.objects.create(name='Root B', slug='r2-root-b')
    child_b = Term.objects.create(name='Child B', slug='r2-child-b', parent=root_b)
    return root_a, root_b, child_b


def test_query_parent_cannot_replace_the_url_parent(operator, two_roots):
    root_a, root_b, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/?parent_id={}'.format(root_a.pk, root_b.pk),
        [{'name': 'Child B renamed', 'slug': 'r2-child-b'}],
        format='json',
    )
    child_b.refresh_from_db()
    assert child_b.name == 'Child B'
    assert response.status_code == 400, response.content[:300]


def test_body_parent_cannot_escape_the_url_parent(operator, two_roots):
    root_a, root_b, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        [{'name': 'New child', 'slug': 'r2-new-child', 'parent_id': root_b.pk}],
        format='json',
    )
    created = Term.objects.filter(slug='r2-new-child').first()
    assert response.status_code == 201, response.content[:400]
    assert created is not None
    assert created.parent_id == root_a.pk, (
        'body parent_id created a child under a foreign parent: {}'.format(created.parent_id)
    )
    assert not Term.objects.filter(parent_id=root_b.pk, slug='r2-new-child').exists()


def test_body_parent_slug_cannot_escape_the_url_parent(operator, two_roots):
    root_a, root_b, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        [{'name': 'Slug child', 'slug': 'r2-slug-child', 'parent__slug': 'r2-root-b'}],
        format='json',
    )
    created = Term.objects.filter(slug='r2-slug-child').first()
    assert response.status_code == 201, response.content[:400]
    assert created is not None
    assert created.parent_id == root_a.pk


def test_nested_children_delete_is_bounded_by_the_url_parent(operator):
    root_a = Term.objects.create(name='Root A', slug='r2-del-a')
    root_b = Term.objects.create(name='Root B', slug='r2-del-b')
    child_a = Term.objects.create(name='Child A', slug='r2-del-child-a', parent=root_a)
    child_b = Term.objects.create(name='Child B', slug='r2-del-child-b', parent=root_b)

    response = operator.delete('/edw/api/terms/{}/children/'.format(root_a.pk))
    survivors = set(Term.objects.values_list('pk', flat=True))

    assert response.status_code == 204, response.content[:300]
    assert child_a.pk not in survivors
    assert {root_a.pk, root_b.pk, child_b.pk} <= survivors


def test_nested_datamart_query_scope_cannot_be_replaced(operator):
    first = DataMart.objects.create(name='First mart', slug='r2-mart-first')
    second = DataMart.objects.create(name='Second mart', slug='r2-mart-second')
    response = operator.post(
        '/edw/api/data-marts/{}/terms/?data_mart_pk={}'.format(first.pk, second.pk),
        [{'name': 'Term', 'slug': 'r2-mart-term'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:300]
    assert not Term.objects.filter(slug='r2-mart-term').exists()


def test_nested_datamart_post_is_scoped_to_the_url_datamart(operator):
    mart = DataMart.objects.create(name='Mart', slug='r2-mart-scope')
    inside = Term.objects.create(name='Inside', slug='r2-inside')
    outside = Term.objects.create(name='Outside', slug='r2-outside')
    mart.terms.add(inside)

    # A slug that exists outside the nested data mart may not be upserted.
    response = operator.post(
        '/edw/api/data-marts/{}/terms/'.format(mart.pk),
        [{'name': 'Escaped', 'slug': 'r2-outside'}],
        format='json',
    )
    outside.refresh_from_db()
    assert outside.name == 'Outside'
    assert response.status_code == 400, response.content[:400]

    # The same request inside the data-mart scope is admitted.
    response = operator.post(
        '/edw/api/data-marts/{}/terms/'.format(mart.pk),
        [{'name': 'Inside renamed', 'slug': 'r2-inside'}],
        format='json',
    )
    inside.refresh_from_db()
    assert response.status_code in (200, 201), response.content[:400]
    assert inside.name == 'Inside renamed'


def test_nested_datamart_delete_is_scoped_to_the_url_datamart(operator):
    mart = DataMart.objects.create(name='Mart', slug='r2-mart-delete')
    inside = Term.objects.create(name='Inside', slug='r2-del-inside')
    outside = Term.objects.create(name='Outside', slug='r2-del-outside')
    mart.terms.add(inside)

    response = operator.delete('/edw/api/data-marts/{}/terms/'.format(mart.pk))
    survivors = set(Term.objects.values_list('pk', flat=True))

    assert response.status_code == 204, response.content[:400]
    assert inside.pk not in survivors
    assert outside.pk in survivors
