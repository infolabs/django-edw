# -*- coding: utf-8 -*-
"""
E7: bulk POST/PUT/PATCH/DELETE against the real InfLabs bulk API.

The runtime test covers:
* collection-level bulk actions registered by the real router;
* scoped whole-batch POST admission (upsert inside the view queryset);
* duplicate/ambiguous identity and new-object natural-key rules;
* permissions checked before any write, with a full rollback when a later
  item is refused;
* atomic failure while applying an admitted batch;
* explicit, default-deny collection DELETE with leaf/restriction policy;
* the same explicit DELETE policy for the data-mart endpoint and the entity
  endpoint (unit-level for the entity policy).
"""
from __future__ import unicode_literals

from unittest import mock

import pytest
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from edw.models.defaults.term import Term
from edw.models.entity import EntityModel
from edw.rest.permissions import IsSuperuserOrReadOnly
from edw.rest.serializers.term import TermDetailSerializer
from edw.tests.contract.app.models import ContractEntity, DataMart
from edw.views.entity import EntityViewSet
from edw.views.term import TermViewSet

pytestmark = pytest.mark.django_db


TERMS_URL = '/edw/api/terms/'
DATA_MARTS_URL = '/edw/api/data-marts/'
ENTITIES_URL = '/edw/api/entities/'


@pytest.fixture
def terms():
    root = Term.objects.create(name='Root', slug='root')
    first = Term.objects.create(name='First', slug='first', parent=root)
    second = Term.objects.create(name='Second', slug='second', parent=root)
    return root, first, second


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


def _slugs():
    return set(Term.objects.values_list('slug', flat=True))


# ---------------------------------------------------------------------- #
# POST / upsert
# ---------------------------------------------------------------------- #
def test_bulk_post_creates_and_upserts_inside_scope(operator, terms):
    root, first, second = terms
    response = operator.post(
        TERMS_URL,
        [
            {'name': 'New term', 'slug': 'new-term'},
            {'name': 'First renamed', 'slug': 'first'},
        ],
        format='json',
    )
    assert response.status_code == 201, response.content[:2000]
    assert Term.objects.filter(slug='new-term').exists()
    assert Term.objects.get(pk=first.pk).name == 'First renamed'
    assert Term.objects.count() == 4


def test_bulk_post_upsert_is_scoped_by_the_view_filter(operator, terms):
    root, first, second = terms
    # The scope names only the root, so "first" is outside the permitted
    # subset; the batch must not touch it and must not create a shadow slug.
    response = operator.post(
        TERMS_URL + '?active=true&parent_id=null',
        [{'name': 'First renamed', 'slug': 'first'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'


def test_bulk_post_duplicate_target_is_refused(operator, terms):
    root, first, second = terms
    response = operator.post(
        TERMS_URL,
        [
            {'name': 'A', 'slug': 'first'},
            {'name': 'B', 'slug': 'first'},
        ],
        format='json',
    )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'


def test_bulk_post_ambiguous_identity_is_refused(operator, terms):
    root, first, second = terms
    # Both identity fields are supplied, but they point at different objects.
    response = operator.post(
        TERMS_URL,
        [{'id': first.pk, 'slug': 'second', 'name': 'Confused'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'
    assert Term.objects.get(pk=second.pk).name == 'Second'


def test_bulk_post_new_object_requires_the_natural_key(db):
    from edw.rest.serializers.term import DataMartBulkListSerializer

    serializer = TermDetailSerializer(many=True)
    with mock.patch.object(
        DataMartBulkListSerializer, 'get_admission_queryset', return_value=Term.objects.none()
    ):
        with pytest.raises(serializers.ValidationError) as error:
            serializer.validate_bulk_create([{'name': 'No slug'}])
    assert 'slug' in str(error.value.detail)


def test_bulk_post_permission_failure_rolls_back_the_complete_batch(operator, terms):
    root, first, second = terms
    original = TermViewSet.check_object_permissions

    def deny_second(view, request, obj):
        if obj.pk == second.pk:
            raise PermissionDenied('object is outside the permitted set')
        return original(view, request, obj)

    with mock.patch.object(TermViewSet, 'check_object_permissions', deny_second):
        response = operator.post(
            TERMS_URL,
            [
                {'name': 'First renamed', 'slug': 'first'},
                {'name': 'Second renamed', 'slug': 'second'},
            ],
            format='json',
        )
    assert response.status_code == 403, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'
    assert Term.objects.get(pk=second.pk).name == 'Second'


def test_bulk_post_failure_while_applying_rolls_back_writes(operator, terms):
    root, first, second = terms
    original = TermDetailSerializer.create
    calls = {'count': 0}

    def flaky_create(self, validated_data):
        calls['count'] += 1
        if calls['count'] == 2:
            raise serializers.ValidationError('second item refused during write')
        return original(self, validated_data)

    with mock.patch.object(TermDetailSerializer, 'create', flaky_create):
        response = operator.post(
            TERMS_URL,
            [
                {'name': 'Fresh one', 'slug': 'fresh-one'},
                {'name': 'Fresh two', 'slug': 'fresh-two'},
            ],
            format='json',
        )
    assert response.status_code == 400, response.content[:2000]
    assert not Term.objects.filter(slug__in=['fresh-one', 'fresh-two']).exists()


def test_nested_term_children_scope_applies_to_bulk_admission(operator, terms):
    root, first, second = terms
    # The nested route scopes the batch to the children of <root>; the root
    # itself is outside that scope and must not be updated by slug upsert.
    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root.pk),
        [{'name': 'Escaped root', 'slug': 'root'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=root.pk).name == 'Root'

    response = operator.post(
        '/edw/api/terms/{}/children/'.format(root.pk),
        [{'name': 'New child', 'slug': 'new-child', 'parent_id': root.pk}],
        format='json',
    )
    assert response.status_code == 201, response.content[:2000]
    assert Term.objects.get(slug='new-child').parent_id == root.pk


# ---------------------------------------------------------------------- #
# PUT / PATCH
# ---------------------------------------------------------------------- #
def test_bulk_put_and_patch(operator, terms):
    root, first, second = terms
    response = operator.put(
        TERMS_URL + '?parent_id={}'.format(root.pk),
        [{'id': first.pk, 'name': 'First full', 'slug': 'first'}],
        format='json',
    )
    assert response.status_code == 200, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First full'

    response = operator.patch(
        TERMS_URL + '?parent_id={}'.format(root.pk),
        [{'id': second.pk, 'name': 'Second patched'}],
        format='json',
    )
    assert response.status_code == 200, response.content[:2000]
    assert Term.objects.get(pk=second.pk).name == 'Second patched'


def test_bulk_put_duplicate_target_is_refused(operator, terms):
    root, first, second = terms
    response = operator.put(
        TERMS_URL,
        [
            {'id': first.pk, 'name': 'A', 'slug': 'first'},
            {'id': first.pk, 'name': 'B', 'slug': 'first'},
        ],
        format='json',
    )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'


def test_bulk_put_target_outside_scope_is_refused(operator, terms):
    root, first, second = terms
    response = operator.patch(
        TERMS_URL + '?parent_id=null',
        [{'id': first.pk, 'name': 'Escaped'}],
        format='json',
    )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'


def test_bulk_put_permission_failure_rolls_back(operator, terms):
    root, first, second = terms
    original = TermViewSet.check_object_permissions

    def deny_second(view, request, obj):
        if obj.pk == second.pk:
            raise PermissionDenied('object is outside the permitted set')
        return original(view, request, obj)

    with mock.patch.object(TermViewSet, 'check_object_permissions', deny_second):
        response = operator.patch(
            TERMS_URL,
            [
                {'id': first.pk, 'name': 'First changed'},
                {'id': second.pk, 'name': 'Second changed'},
            ],
            format='json',
        )
    assert response.status_code == 403, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'
    assert Term.objects.get(pk=second.pk).name == 'Second'


def test_bulk_put_failure_while_applying_rolls_back(operator, terms):
    root, first, second = terms
    original = TermDetailSerializer.update
    calls = {'count': 0}

    def flaky_update(self, instance, validated_data):
        calls['count'] += 1
        if calls['count'] == 2:
            raise serializers.ValidationError('second item refused during write')
        return original(self, instance, validated_data)

    with mock.patch.object(TermDetailSerializer, 'update', flaky_update):
        response = operator.patch(
            TERMS_URL,
            [
                {'id': first.pk, 'name': 'First changed'},
                {'id': second.pk, 'name': 'Second changed'},
            ],
            format='json',
        )
    assert response.status_code == 400, response.content[:2000]
    assert Term.objects.get(pk=first.pk).name == 'First'
    assert Term.objects.get(pk=second.pk).name == 'Second'


# ---------------------------------------------------------------------- #
# DELETE
# ---------------------------------------------------------------------- #
def test_collection_delete_is_default_denied(operator, terms):
    response = operator.delete(TERMS_URL)
    assert response.status_code == 400
    assert Term.objects.count() == 3


def test_collection_delete_of_leaf_is_allowed(operator, terms):
    root, first, second = terms
    response = operator.delete(TERMS_URL + '?active=true&parent_id={}'.format(root.pk))
    assert response.status_code == 204, response.content[:2000]
    assert not Term.objects.filter(pk__in=[first.pk, second.pk]).exists()
    assert Term.objects.filter(pk=root.pk).exists()


def test_collection_delete_never_cascades_through_a_parent(operator, terms):
    root, first, second = terms
    response = operator.delete(TERMS_URL + '?active=true&parent_id=null')
    assert response.status_code == 400
    assert Term.objects.count() == 3


def test_collection_delete_respects_delete_restriction(operator, terms):
    root, first, second = terms
    protected = Term.objects.create(
        name='Protected', slug='protected', system_flags=Term.system_flags.delete_restriction
    )
    response = operator.delete(TERMS_URL + '?active=true&slug=protected')
    assert response.status_code == 400
    assert Term.objects.filter(pk=protected.pk).exists()


def test_collection_delete_requires_the_view_permission(api_client, regular_user, terms):
    api_client.force_authenticate(user=regular_user)
    response = api_client.delete(TERMS_URL + '?active=true&slug=first')
    assert response.status_code == 403
    assert Term.objects.filter(slug='first').exists()


def test_datamart_collection_delete_policy(operator):
    root = DataMart.objects.create(name='Root mart', slug='root-mart')
    leaf = DataMart.objects.create(name='Leaf mart', slug='leaf-mart', parent=root)

    assert operator.delete(DATA_MARTS_URL).status_code == 400
    assert operator.delete(DATA_MARTS_URL + '?active=true&parent_id=null').status_code == 400
    assert DataMart.objects.count() == 2

    response = operator.delete(DATA_MARTS_URL + '?active=true&slug=leaf-mart')
    assert response.status_code == 204, response.content[:2000]
    assert not DataMart.objects.filter(pk=leaf.pk).exists()
    assert DataMart.objects.filter(pk=root.pk).exists()


# ---------------------------------------------------------------------- #
# Entity endpoint: explicit policy, real bulk PATCH and permission checks
# ---------------------------------------------------------------------- #
def _entity_patch_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def test_entity_bulk_patch_uses_view_and_object_permissions(api_client, superuser, entity_types):
    original_permissions = ContractEntity._rest_meta.permission_classes
    ContractEntity._rest_meta.permission_classes = [IsSuperuserOrReadOnly]
    try:
        entity = ContractEntity.objects.create(name='Entity')
        client = _entity_patch_client(api_client, superuser)
        response = client.patch(
            ENTITIES_URL,
            [{'id': entity.pk, 'description': 'patched'}],
            format='json',
        )
        assert response.status_code == 200, response.content[:2000]
        entity.refresh_from_db()
        assert entity.description == 'patched'
    finally:
        ContractEntity._rest_meta.permission_classes = original_permissions


def test_entity_write_is_denied_without_model_write_permission(api_client, superuser, entity_types):
    entity = ContractEntity.objects.create(name='Entity')
    client = _entity_patch_client(api_client, superuser)
    response = client.patch(ENTITIES_URL, [{'id': entity.pk, 'description': 'patched'}], format='json')
    assert response.status_code == 403
    entity.refresh_from_db()
    assert entity.description == ''


def test_entity_bulk_delete_policy_is_explicit_and_deny_by_default(api_client, superuser, entity_types):
    from django.test import RequestFactory

    view = EntityViewSet()
    view.request = RequestFactory().delete('/entities/')
    view.request.user = superuser
    view.request.GET = view.request.GET.copy()
    view.request.GET['_data_mart_permissions'] = {
        'can_add': True, 'can_change': True, 'can_delete': True, 'has_owner': False,
    }
    view.kwargs = {}
    ContractEntity.objects.create(name='Entity')
    filtered = EntityModel.objects.all()

    # No explicit data-mart scope: root permission alone never authorizes.
    assert view.allow_bulk_destroy(filtered, filtered) is False

    data_mart = DataMart.objects.create(name='Mart', slug='mart')
    view.kwargs = {'data_mart_pk': str(data_mart.pk)}
    assert view.allow_bulk_destroy(filtered, filtered) is True

    view.request.GET['_data_mart_permissions'] = {
        'can_add': True, 'can_change': True, 'can_delete': False, 'has_owner': True,
    }
    assert view.allow_bulk_destroy(filtered, filtered) is False
