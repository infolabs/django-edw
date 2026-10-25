# -*- coding: utf-8 -*-
"""E11/R1/R2 (ported E10.safetycheck): R2 nested URL scope bounds every write method."""
from __future__ import unicode_literals

import pytest
from rest_framework.test import APIClient

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import DataMart

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'
DATA_MARTS_URL = '/edw/api/data-marts/'


@pytest.fixture
def two_roots():
    root_a = Term.objects.create(name='Root A', slug='r2-root-a')
    root_b = Term.objects.create(name='Root B', slug='r2-root-b')
    child_b = Term.objects.create(name='Child B', slug='r2-child-b', parent=root_b)
    child_a = Term.objects.create(name='Child A', slug='r2-child-a', parent=root_a)
    return root_a, root_b, child_a, child_b


def test_nested_query_parent_cannot_replace_the_url_parent(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/?parent_id={}'.format(root_a.pk, root_b.pk),
        [{'name': 'Child B renamed', 'slug': 'r2-child-b'}],
        format='json',
    )
    child_b.refresh_from_db()
    assert child_b.name == 'Child B', 'foreign child was modified: {}'.format(child_b.name)
    assert response.status_code == 400, response.content[:300]


def test_nested_body_parent_cannot_escape_the_url_parent_bulk(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        [{'name': 'New child', 'slug': 'r2-new-child', 'parent_id': root_b.pk}],
        format='json',
    )
    created = Term.objects.filter(slug='r2-new-child').first()
    assert response.status_code == 201, response.content[:400]
    assert created is not None and created.parent_id == root_a.pk, (
        'body parent_id created a child under a foreign parent: {}'.format(
            getattr(created, 'parent_id', None)))


def test_nested_body_parent_slug_cannot_escape_the_url_parent_bulk(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        [{'name': 'Slug child', 'slug': 'r2-slug-child', 'parent__slug': 'r2-root-b'}],
        format='json',
    )
    created = Term.objects.filter(slug='r2-slug-child').first()
    assert response.status_code == 201, response.content[:400]
    assert created is not None and created.parent_id == root_a.pk, (
        'body parent__slug created a child under a foreign parent: {}'.format(
            getattr(created, 'parent_id', None)))


def test_nested_body_parent_cannot_escape_the_url_parent_single_object(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        {'name': 'Single child', 'slug': 'r2-single-child', 'parent_id': root_b.pk},
        format='json',
    )
    created = Term.objects.filter(slug='r2-single-child').first()
    assert response.status_code in (200, 201), response.content[:400]
    assert created is not None and created.parent_id == root_a.pk, (
        'single-object body parent_id escaped the URL parent: {}'.format(
            getattr(created, 'parent_id', None)))


def test_nested_detail_patch_of_foreign_child_is_bounded(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.patch(
        '/edw/api/terms/{}/children/{}/'.format(root_a.pk, child_b.pk),
        {'name': 'Hijacked'},
        format='json',
    )
    child_b.refresh_from_db()
    child_a.refresh_from_db()
    assert child_b.name == 'Child B', 'foreign child modified through nested URL parent'
    assert child_a.name == 'Child A'
    assert response.status_code in (400, 403, 404), response.content[:300]


def test_nested_detail_delete_of_foreign_child_is_bounded(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.delete(
        '/edw/api/terms/{}/children/{}/'.format(root_a.pk, child_b.pk))
    assert Term.objects.filter(pk=child_b.pk).exists(), 'foreign child deleted through nested URL'
    assert response.status_code in (400, 403, 404), response.content[:300]


def test_nested_detail_patch_body_parent_cannot_escape(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.patch(
        '/edw/api/terms/{}/children/{}/'.format(root_a.pk, child_a.pk),
        {'name': 'Child A renamed', 'parent_id': root_b.pk},
        format='json',
    )
    child_a.refresh_from_db()
    assert response.status_code in (200, 204), response.content[:400]
    assert child_a.name == 'Child A renamed'
    assert child_a.parent_id == root_a.pk, (
        'body parent_id moved the child outside the URL parent: {}'.format(child_a.parent_id))


def test_nested_detail_delete_of_the_named_child_is_allowed(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.delete(
        '/edw/api/terms/{}/children/{}/'.format(root_a.pk, child_a.pk))
    assert response.status_code == 204, response.content[:300]
    assert not Term.objects.filter(pk=child_a.pk).exists()
    assert Term.objects.filter(pk=child_b.pk).exists()


def test_nested_nonexistent_int_parent_does_not_write_a_foreign_row(superuser):
    before = set(Term.objects.values_list('pk', flat=True))
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user=superuser)
    response = client.post(
        '/edw/api/terms/999999/children/',
        [{'name': 'Orphan', 'slug': 'r2-orphan'}],
        format='json',
    )
    after = set(Term.objects.values_list('pk', flat=True))
    assert after == before, 'a write succeeded under a non-existent URL parent'
    assert not Term.objects.filter(slug='r2-orphan').exists()
    assert response.status_code != 500, (
        'non-existent integer URL parent produced a server error: {} {}'.format(
            response.status_code, response.content[:300]))


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


def test_nested_datamart_post_is_bounded_to_the_url_mart(operator):
    mart = DataMart.objects.create(name='Mart', slug='r2-mart-scope')
    inside = Term.objects.create(name='Inside', slug='r2-inside')
    outside = Term.objects.create(name='Outside', slug='r2-outside')
    mart.terms.add(inside)
    response = operator.post(
        '/edw/api/data-marts/{}/terms/'.format(mart.pk),
        [{'name': 'Escaped', 'slug': 'r2-outside'}],
        format='json',
    )
    outside.refresh_from_db()
    assert outside.name == 'Outside'
    assert response.status_code == 400, response.content[:400]


def test_nested_datamart_detail_patch_of_foreign_term_is_bounded(operator):
    mart = DataMart.objects.create(name='Mart', slug='r2-mart-detail')
    inside = Term.objects.create(name='Inside', slug='r2-detail-inside')
    outside = Term.objects.create(name='Outside', slug='r2-detail-outside')
    mart.terms.add(inside)
    response = operator.patch(
        '/edw/api/data-marts/{}/terms/{}/'.format(mart.pk, outside.pk),
        {'name': 'Hijacked'},
        format='json',
    )
    outside.refresh_from_db()
    assert outside.name == 'Outside', 'term outside the URL data mart was modified'
    assert response.status_code in (400, 403, 404), response.content[:300]


def test_nested_bulk_patch_cannot_target_a_foreign_child(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.patch(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        [{'id': child_b.pk, 'name': 'Bulk hijack'}],
        format='json',
    )
    child_b.refresh_from_db()
    child_a.refresh_from_db()
    assert child_b.name == 'Child B', 'bulk PATCH reached a child outside the URL parent'
    assert child_a.name == 'Child A'
    assert response.status_code in (400, 403, 404), response.content[:300]


def test_nested_bulk_patch_body_parent_cannot_escape(operator, two_roots):
    root_a, root_b, child_a, child_b = two_roots
    response = operator.patch(
        '/edw/api/terms/{}/children/'.format(root_a.pk),
        [{'id': child_a.pk, 'name': 'Bulk renamed', 'parent_id': root_b.pk}],
        format='json',
    )
    child_a.refresh_from_db()
    assert response.status_code in (200, 204), response.content[:400]
    assert child_a.name == 'Bulk renamed'
    assert child_a.parent_id == root_a.pk, (
        'bulk PATCH body parent_id moved the child outside the URL parent: {}'.format(
            child_a.parent_id))
