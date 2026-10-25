# -*- coding: utf-8 -*-
"""E11/R4 (ported E10.safetycheck): DELETE effect set (bulk and detail)."""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term
from edw.models.related import AdditionalEntityCharacteristicOrMarkModel
from edw.tests.contract.app.models import (
    ContractEntity,
    DataMart,
    DataMartPermission,
    FastDeleteProbe,
    ProtectedProbe,
    SafetyProbeFlags,
    UnknownEffectProbe,
)

pytestmark = pytest.mark.django_db

TERMS_URL = '/edw/api/terms/'
DATA_MARTS_URL = '/edw/api/data-marts/'


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def probes():
    """Probe flags are per-test and always restored."""
    SafetyProbeFlags.refuse_count = False
    SafetyProbeFlags.refuse_fetch = False
    yield SafetyProbeFlags
    SafetyProbeFlags.refuse_count = False
    SafetyProbeFlags.refuse_fetch = False


def _term_pks():
    return set(Term.objects.values_list('pk', flat=True))


def test_bulk_delete_of_leaf_with_related_cascade_is_refused(operator, entity_types):
    root = Term.objects.create(name='Cascade root', slug='r4-cascade-root')
    leaf = Term.objects.create(name='Cascade leaf', slug='r4-cascade-leaf', parent=root)
    clean_leaf = Term.objects.create(name='Clean leaf', slug='r4-clean-leaf', parent=root)
    entity = ContractEntity.objects.create(name='Cascade entity')
    dependent = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        term=leaf, entity=entity, value='v1')
    before = _term_pks()
    response = operator.delete(TERMS_URL + '?parent_id={}'.format(root.pk))
    after = _term_pks()
    assert after == before, 'leaf DELETE cascaded or partially deleted: {}'.format(before - after)
    assert AdditionalEntityCharacteristicOrMarkModel.objects.filter(pk=dependent.pk).exists()
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_term_with_related_cascade_is_refused(operator, entity_types):
    term = Term.objects.create(name='Detail dependent', slug='r4-detail-dependent')
    entity = ContractEntity.objects.create(name='Detail entity')
    dependent = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        term=term, entity=entity, value='v2')
    response = operator.delete(TERMS_URL + '{}/'.format(term.pk))
    assert Term.objects.filter(pk=term.pk).exists(), 'detail DELETE removed the named term'
    assert AdditionalEntityCharacteristicOrMarkModel.objects.filter(pk=dependent.pk).exists()
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_a_term_root_does_not_cascade_the_subtree(operator):
    root = Term.objects.create(name='Detail root', slug='r4-detail-root')
    child = Term.objects.create(name='Detail child', slug='r4-detail-child', parent=root)
    grand = Term.objects.create(name='Detail grand', slug='r4-detail-grand', parent=child)
    response = operator.delete(TERMS_URL + '{}/'.format(root.pk))
    assert {root.pk, child.pk, grand.pk} <= _term_pks()
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_a_datamart_root_does_not_cascade_the_subtree(operator):
    root = DataMart.objects.create(name='Mart root', slug='r4-mart-root')
    child = DataMart.objects.create(name='Mart child', slug='r4-mart-child', parent=root)
    response = operator.delete(DATA_MARTS_URL + '{}/'.format(root.pk))
    assert DataMart.objects.filter(pk__in=[root.pk, child.pk]).count() == 2
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_a_leaf_without_effects_is_allowed(operator):
    root = Term.objects.create(name='Leaf root', slug='r4-leaf-root')
    leaf = Term.objects.create(name='Leaf', slug='r4-leaf', parent=root)
    response = operator.delete(TERMS_URL + '{}/'.format(leaf.pk))
    assert response.status_code == 204, response.content[:300]
    assert not Term.objects.filter(pk=leaf.pk).exists()
    assert Term.objects.filter(pk=root.pk).exists()


def test_detail_delete_of_datamart_with_permission_rows_is_refused(operator, superuser):
    from edw.models.defaults.customer import Customer

    customer = Customer.objects.create(user=superuser, salutation='na')
    mart = DataMart.objects.create(name='Permission mart', slug='r4-mart-perm')
    DataMartPermission.objects.create(
        data_mart=mart, customer=customer, can_add=True, can_change=True, can_delete=True)
    response = operator.delete(DATA_MARTS_URL + '{}/'.format(mart.pk))
    assert DataMart.objects.filter(pk=mart.pk).exists(), 'detail DELETE ignored permission rows'
    assert DataMartPermission.objects.filter(data_mart_id=mart.pk).exists()
    assert response.status_code == 400, response.content[:300]


def test_shared_term_delete_removes_foreign_mart_membership_silently(operator):
    """R4: auto-created M2M through rows are part of the effect set.

    Deleting a term that belongs to a *foreign* data mart removes the
    data-mart membership row without naming/authorizing that mart.  Under R4 a
    not-proven-safe through-row policy must default-deny (400, no deletion).
    """
    mart = DataMart.objects.create(name='Foreign mart', slug='r4-foreign-mart')
    term = Term.objects.create(name='Shared term', slug='r4-shared-term')
    mart.terms.add(term)
    through = DataMart.terms.through
    assert through.objects.filter(term_id=term.pk).count() == 1
    response = operator.delete(TERMS_URL + '{}/'.format(term.pk))
    term_left = Term.objects.filter(pk=term.pk).exists()
    through_left = through.objects.filter(term_id=term.pk).count()
    assert term_left, (
        'foreign-mart membership consequence was ignored: term deleted, '
        'through rows left={}, status={}'.format(through_left, response.status_code))
    assert through_left == 1, 'foreign-mart through row was deleted without authorization'
    assert response.status_code == 400, response.content[:300]


def test_fast_delete_count_exception_is_not_treated_as_zero(operator, probes):
    """R4: an exception while counting a fast-delete effect set is not "0 rows".

    The related model has no signals/cascades, so Django's collector keeps its
    queryset in ``fast_deletes``.  The probe refuses ``count()``; the code under
    test must refuse the delete (fail-closed) instead of treating the failed
    count as an empty effect set.
    """
    term = Term.objects.create(name='Fast-delete term', slug='r4-fast-term')
    probe = FastDeleteProbe.objects.create(term=term, note='probe')
    probes.refuse_count = True
    response = operator.delete(TERMS_URL + '{}/'.format(term.pk))
    assert Term.objects.filter(pk=term.pk).exists(), (
        'detail DELETE removed the term although the related fast-delete '
        'effect set could not be counted (status={})'.format(response.status_code))
    assert FastDeleteProbe.objects.filter(pk=probe.pk).exists(), (
        'related fast-delete row was removed without an authorized effect set')
    assert response.status_code == 400, response.content[:300]


def test_unmeasurable_effect_set_is_refused(operator, probes):
    """R4: if the effect set cannot be measured at all, nothing is deleted.

    The effect rows themselves cannot be read; the request must be refused
    (never "no related rows").  This control uses a *clean* leaf so a positive
    deletion would otherwise be allowed.
    """
    root = Term.objects.create(name='Unknown root', slug='r4-unknown-root')
    leaf = Term.objects.create(name='Unknown leaf', slug='r4-unknown-leaf', parent=root)
    probes.refuse_fetch = True
    response = operator.delete(TERMS_URL + '{}/'.format(leaf.pk))
    assert Term.objects.filter(pk=leaf.pk).exists(), (
        'detail DELETE removed the term although the effect set could not be measured')
    assert response.status_code == 400, response.content[:300]


def test_entity_detail_delete_with_related_characteristic_is_refused(
        operator, entity_types):
    """R4 also covers the existing writable Entity related path.

    An entity that owns a characteristic row must not be deleted through the
    root/superuser permission alone: the related row is an implicit effect.
    """
    entity = ContractEntity.objects.create(name='Effect entity')
    term = entity_types['child']
    dependent = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        entity=entity, term=term, value='v-effect')
    response = operator.delete('/probe/entities/{}/'.format(entity.pk))
    assert ContractEntity.objects.filter(pk=entity.pk).exists(), (
        'entity DELETE ignored a related characteristic row')
    assert AdditionalEntityCharacteristicOrMarkModel.objects.filter(pk=dependent.pk).exists()
    assert response.status_code == 400, response.content[:300]


def test_detail_delete_of_term_with_protected_related_row_is_refused(operator):
    """R4: a PROTECT relation is an effect the named permission cannot override."""
    term = Term.objects.create(name='Protected term', slug='r4-protected-term')
    protected = ProtectedProbe.objects.create(term=term, note='keep')
    response = operator.delete(TERMS_URL + '{}/'.format(term.pk))
    assert Term.objects.filter(pk=term.pk).exists(), 'detail DELETE ignored PROTECT'
    assert ProtectedProbe.objects.filter(pk=protected.pk).exists()
    assert response.status_code == 400, response.content[:300]


def test_collection_delete_of_leaf_with_protected_related_row_is_refused(operator):
    leaf = Term.objects.create(name='Protected leaf', slug='r4-protected-leaf')
    protected = ProtectedProbe.objects.create(term=leaf, note='keep')
    response = operator.delete(TERMS_URL + '?parent_id=null')
    assert Term.objects.filter(pk=leaf.pk).exists(), 'collection DELETE ignored PROTECT'
    assert ProtectedProbe.objects.filter(pk=protected.pk).exists()
    assert response.status_code == 400, response.content[:300]
