# -*- coding: utf-8 -*-
"""
E7: filter backends actually change the queryset.

Covered contract:
* a regular declared parameter (``slug``);
* a method filter (``parent_id`` with ``null`` meaning the tree root);
* a negated value (``active=false``) and an empty value (removed, no filter);
* pre-existing queryset/permission constraints are preserved by the backend;
* the explicit legacy ``filter_class`` path still works and rejects a
  non-filterset attribute.
"""
from __future__ import unicode_literals

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from edw.models.defaults.term import Term
from edw.rest.filters.backends import EDWFilterBackend
from edw.rest.filters.term import TermFilter

pytestmark = pytest.mark.django_db


TERMS_URL = '/edw/api/terms/'


@pytest.fixture
def terms():
    root = Term.objects.create(name='Root', slug='root', active=True)
    active_child = Term.objects.create(name='Active child', slug='active-child', parent=root, active=True)
    inactive_child = Term.objects.create(name='Inactive child', slug='inactive-child', parent=root, active=False)
    return root, active_child, inactive_child


def _results(response):
    assert response.status_code == 200, response.content[:2000]
    payload = response.json()
    return payload['results'], payload['count']


def test_regular_parameter_filters_the_view(api_client, terms):
    results, count = _results(api_client.get(TERMS_URL, {'active': 'true'}))
    assert count == 2
    assert {item['slug'] for item in results} == {'root', 'active-child'}


def test_method_filter_parent_id(api_client, terms):
    root, active_child, inactive_child = terms
    results, count = _results(api_client.get(TERMS_URL, {'parent_id': root.pk}))
    assert count == 2
    assert {item['slug'] for item in results} == {'active-child', 'inactive-child'}

    roots, count = _results(api_client.get(TERMS_URL, {'parent_id': 'null'}))
    assert count == 1
    assert [item['slug'] for item in roots] == ['root']


def test_negated_and_empty_values(api_client, terms):
    results, count = _results(api_client.get(TERMS_URL, {'active': 'false'}))
    assert count == 1
    assert [item['slug'] for item in results] == ['inactive-child']

    # The view removes empty query parameters before filtering: an empty value
    # is "no filter", not "match the empty string".
    results, count = _results(api_client.get(TERMS_URL, {'active': ''}))
    assert count == 3


class _FiltersetProbeView(object):
    filterset_class = TermFilter


class _LegacyProbeView(object):
    filter_class = TermFilter


class _BrokenLegacyProbeView(object):
    filter_class = object


def _backend_queryset(view, query, queryset):
    request = Request(APIRequestFactory().get('/?' + query))
    return EDWFilterBackend().filter_queryset(request, queryset, view)


def test_legacy_filter_class_is_explicit_and_works(terms):
    queryset = Term.objects.all()
    filtered = _backend_queryset(_LegacyProbeView(), 'active=false', queryset)
    assert [term.slug for term in filtered] == ['inactive-child']
    # No silent fallback for a non-filterset attribute.
    with pytest.raises(TypeError):
        _backend_queryset(_BrokenLegacyProbeView(), 'active=false', queryset)


def test_backend_preserves_queryset_constraints(terms):
    root, active_child, inactive_child = terms
    # The caller's restriction is part of the security/scope contract and must
    # survive the filterset, even when the query parameter would match.
    restricted = Term.objects.filter(active=True)
    filtered = _backend_queryset(_FiltersetProbeView(), 'active=false', restricted)
    assert list(filtered) == []

    only_child = Term.objects.filter(pk=active_child.pk)
    filtered = _backend_queryset(_FiltersetProbeView(), 'active=true', only_child)
    assert [term.pk for term in filtered] == [active_child.pk]


def test_permissions_are_not_a_filter_bypass(api_client, terms, regular_user):
    # Read access stays open, while write access is decided by the view
    # permission before any filter or serializer runs.
    assert api_client.get(TERMS_URL, {'slug': 'root'}).status_code == 200
    api_client.force_authenticate(user=regular_user)
    response = api_client.post(
        TERMS_URL, [{'name': 'Injected', 'slug': 'injected'}], format='json'
    )
    assert response.status_code == 403
    assert not Term.objects.filter(slug='injected').exists()
