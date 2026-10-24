# -*- coding: utf-8 -*-
"""
E9/R4: collection and detail DELETE authorize the complete effect set.

Ports the E8 counter-examples into the product regression gate:

* a leaf DELETE that would also remove related CASCADE rows (characteristics /
  marks) is refused as a whole batch, with no partial delete;
* a detail DELETE of a tree root is refused instead of cascading the subtree
  with only root permission;
* the same rule applies to a data-mart tree;
* a plain leaf detail DELETE still works, and per-object delete callbacks keep
  their atomic rollback semantics.
"""
from __future__ import unicode_literals

from unittest import mock

import pytest

from edw.models.defaults.term import Term
from edw.models.related import AdditionalEntityCharacteristicOrMarkModel
from edw.tests.contract.app.models import ContractEntity, DataMart
from edw.views.term import TermViewSet

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'
DATA_MARTS_URL = '/edw/api/data-marts/'


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


def test_bulk_delete_of_leaf_with_related_cascade_is_refused(operator, entity_types):
    root = Term.objects.create(name='Cascade root', slug='r4-cascade-root')
    leaf = Term.objects.create(name='Cascade leaf', slug='r4-cascade-leaf', parent=root)
    clean_leaf = Term.objects.create(name='Clean leaf', slug='r4-clean-leaf', parent=root)
    entity = ContractEntity.objects.create(name='Cascade entity')
    dependent = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        term=leaf, entity=entity, value='v1'
    )

    response = operator.delete(TERMS_URL + '?parent_id={}'.format(root.pk))
    dependent_left = AdditionalEntityCharacteristicOrMarkModel.objects.filter(pk=dependent.pk).exists()
    term_left = Term.objects.filter(pk=leaf.pk).exists()
    clean_left = Term.objects.filter(pk=clean_leaf.pk).exists()

    assert dependent_left and term_left and clean_left, (
        'leaf DELETE cascaded into dependent objects or partially deleted the batch: '
        'status={} term_left={} dependent_left={} clean_left={}'.format(
            response.status_code, term_left, dependent_left, clean_left
        )
    )
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_a_root_does_not_cascade_the_subtree(operator):
    root = Term.objects.create(name='Detail root', slug='r4-detail-root')
    child = Term.objects.create(name='Detail child', slug='r4-detail-child', parent=root)
    grand = Term.objects.create(name='Detail grand', slug='r4-detail-grand', parent=child)

    response = operator.delete(TERMS_URL + '{}/'.format(root.pk))
    survivors = set(Term.objects.values_list('pk', flat=True))

    assert {root.pk, child.pk, grand.pk} <= survivors, (
        'detail DELETE of a root cascaded the subtree: status={} survivors={}'.format(
            response.status_code, survivors
        )
    )
    assert response.status_code == 400, response.content[:300]


def test_datamart_detail_delete_of_a_root_does_not_cascade_the_subtree(operator):
    root = DataMart.objects.create(name='Detail mart root', slug='r4-mart-root')
    child = DataMart.objects.create(name='Detail mart child', slug='r4-mart-child', parent=root)

    response = operator.delete(DATA_MARTS_URL + '{}/'.format(root.pk))
    survivors = set(DataMart.objects.values_list('pk', flat=True))

    assert {root.pk, child.pk} <= survivors
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_a_leaf_without_effects_is_allowed(operator):
    root = Term.objects.create(name='Leaf root', slug='r4-leaf-root')
    leaf = Term.objects.create(name='Leaf', slug='r4-leaf', parent=root)

    response = operator.delete(TERMS_URL + '{}/'.format(leaf.pk))
    assert not Term.objects.filter(pk=leaf.pk).exists()
    assert Term.objects.filter(pk=root.pk).exists()
    assert response.status_code == 204, response.content[:300]


def test_per_object_delete_callbacks_keep_the_batch_atomic(operator):
    root = Term.objects.create(name='Callback root', slug='r4-callback-root')
    first = Term.objects.create(name='First', slug='r4-callback-first', parent=root)
    second = Term.objects.create(name='Second', slug='r4-callback-second', parent=root)

    original = TermViewSet.perform_destroy
    calls = {'count': 0}

    def flaky(view, instance):
        calls['count'] += 1
        original(view, instance)
        if calls['count'] == 2:
            raise RuntimeError('late delete failure')

    with mock.patch.object(TermViewSet, 'perform_destroy', flaky):
        with pytest.raises(RuntimeError):
            operator.delete(TERMS_URL + '?parent_id={}'.format(root.pk))

    survivors = set(Term.objects.values_list('pk', flat=True))
    assert calls['count'] == 2, 'per-object delete callback was not called per target'
    assert {first.pk, second.pk} <= survivors, 'late failure left committed deletions'
