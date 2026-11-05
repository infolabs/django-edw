# -*- coding: utf-8 -*-
"""E12.residualcheck: independent S2/R4 DELETE effect-set controls."""
from __future__ import unicode_literals

import pytest

from edw.models.defaults.term import Term
from edw.models.related import AdditionalEntityCharacteristicOrMarkModel
from edw.tests.contract.app.models import (
    ContractEntity,
    DataMart,
    FastDeleteProbe,
    ProtectedProbe,
    SafetyProbeFlags,
    UnknownEffectProbe,
)

pytestmark = pytest.mark.django_db

TERMS = '/edw/api/terms/'
DATA_MARTS = '/edw/api/data-marts/'


@pytest.fixture
def probes():
    SafetyProbeFlags.refuse_count = False
    SafetyProbeFlags.refuse_fetch = False
    yield SafetyProbeFlags
    SafetyProbeFlags.refuse_count = False
    SafetyProbeFlags.refuse_fetch = False


def term_states():
    return {
        term.pk: (term.name, term.slug, term.parent_id)
        for term in Term.objects.all()
    }


def through_rows():
    through = DataMart.terms.through
    return sorted(through.objects.values_list('datamart_id', 'term_id'))


def test_foreign_mart_membership_delete_is_refused(operator):
    mart = DataMart.objects.create(name='Foreign mart', slug='e12-foreign-mart')
    term = Term.objects.create(name='Shared term', slug='e12-shared-term')
    mart.terms.add(term)
    before_terms = term_states()
    before_rows = through_rows()
    assert before_rows == [(mart.pk, term.pk)]
    response = operator.delete(TERMS + '{}/'.format(term.pk))
    after_terms = term_states()
    after_rows = through_rows()
    assert after_terms == before_terms, 'the term was deleted despite the foreign membership'
    assert after_rows == before_rows, 'the foreign through row was removed'
    assert response.status_code == 400, response.content[:400]


def test_shared_term_in_two_marts_with_one_named_is_refused(operator):
    first = DataMart.objects.create(name='First mart', slug='e12-first-mart')
    second = DataMart.objects.create(name='Second mart', slug='e12-second-mart')
    term = Term.objects.create(name='Two marts term', slug='e12-two-marts-term')
    first.terms.add(term)
    second.terms.add(term)
    before_terms = term_states()
    before_rows = through_rows()
    assert len(before_rows) == 2
    response = operator.delete(
        DATA_MARTS + '{}/terms/{}/'.format(first.pk, term.pk))
    after_terms = term_states()
    after_rows = through_rows()
    assert after_terms == before_terms, (
        'the term was deleted although the second membership was not named')
    assert after_rows == before_rows, (
        'a foreign through row was removed although only one mart was named')
    assert response.status_code == 400, response.content[:400]


def test_named_single_mart_membership_delete_is_allowed(operator):
    mart = DataMart.objects.create(name='Named mart', slug='e12-named-mart')
    term = Term.objects.create(name='Named membership term',
                               slug='e12-named-membership')
    mart.terms.add(term)
    assert through_rows() == [(mart.pk, term.pk)]
    response = operator.delete(
        DATA_MARTS + '{}/terms/{}/'.format(mart.pk, term.pk))
    after_terms = term_states()
    after_rows = through_rows()
    assert term.pk not in after_terms, (
        'the explicitly authorized named-membership delete did not remove the term')
    assert after_rows == [], 'the authorized through row was not removed'
    assert response.status_code == 204, response.content[:400]
    assert DataMart.objects.filter(pk=mart.pk).exists()


def test_fast_delete_measurement_error_is_fail_closed(operator, probes):
    term = Term.objects.create(name='Fast term', slug='e12-fast-term')
    probe = FastDeleteProbe.objects.create(term=term, note='keep')
    before_terms = term_states()
    probes.refuse_fetch = True
    response = operator.delete(TERMS + '{}/'.format(term.pk))
    probes.refuse_fetch = False
    after_terms = term_states()
    probe_left = FastDeleteProbe.objects.filter(pk=probe.pk).exists()
    assert after_terms == before_terms, (
        'a failed fast-delete measurement was treated as an empty effect set')
    assert probe_left, 'the related fast-delete row was removed'
    assert response.status_code == 400, response.content[:400]


def test_unmeasurable_clean_leaf_effect_set_is_refused(operator, probes):
    root = Term.objects.create(name='Unknown root', slug='e12-unknown-root')
    leaf = Term.objects.create(name='Unknown leaf', slug='e12-unknown-leaf',
                               parent=root)
    UnknownEffectProbe.objects.create(term=leaf, note='keep')
    before_terms = term_states()
    probes.refuse_fetch = True
    response = operator.delete(TERMS + '{}/'.format(leaf.pk))
    probes.refuse_fetch = False
    after_terms = term_states()
    assert after_terms == before_terms, 'the leaf was deleted without a measured effect set'
    assert response.status_code == 400, response.content[:400]


def test_protected_related_row_is_refused(operator):
    term = Term.objects.create(name='Protected term', slug='e12-protected-term')
    protected = ProtectedProbe.objects.create(term=term, note='keep')
    before_terms = term_states()
    response = operator.delete(TERMS + '{}/'.format(term.pk))
    after_terms = term_states()
    assert after_terms == before_terms, 'PROTECT was bypassed'
    assert ProtectedProbe.objects.filter(pk=protected.pk).exists()
    assert response.status_code == 400, response.content[:400]


def test_cascade_related_row_is_refused(operator, entity_types):
    term = Term.objects.create(name='Cascade term', slug='e12-cascade-term')
    entity = ContractEntity.objects.create(name='Cascade entity')
    dependent = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        term=term, entity=entity, value='v')
    before_terms = term_states()
    response = operator.delete(TERMS + '{}/'.format(term.pk))
    after_terms = term_states()
    assert after_terms == before_terms, 'a CASCADE related row was removed implicitly'
    assert AdditionalEntityCharacteristicOrMarkModel.objects.filter(
        pk=dependent.pk).exists()
    assert response.status_code == 400, response.content[:400]


def test_detail_root_delete_does_not_cascade_the_subtree(operator):
    root = Term.objects.create(name='Subtree root', slug='e12-subtree-root')
    child = Term.objects.create(name='Subtree child', slug='e12-subtree-child',
                                parent=root)
    grand = Term.objects.create(name='Subtree grand', slug='e12-subtree-grand',
                                parent=child)
    before_terms = term_states()
    response = operator.delete(TERMS + '{}/'.format(root.pk))
    after_terms = term_states()
    assert after_terms == before_terms, 'the MPTT subtree was cascaded'
    assert response.status_code == 400, response.content[:400]


def test_detail_delete_of_clean_leaf_is_allowed(operator):
    root = Term.objects.create(name='Clean root', slug='e12-clean-root')
    leaf = Term.objects.create(name='Clean leaf', slug='e12-clean-leaf',
                               parent=root)
    response = operator.delete(TERMS + '{}/'.format(leaf.pk))
    assert not Term.objects.filter(pk=leaf.pk).exists()
    assert Term.objects.filter(pk=root.pk).exists()
    assert response.status_code == 204, response.content[:400]


def test_collection_delete_with_declared_leaf_scope_is_allowed(operator):
    root = Term.objects.create(name='Bulk root', slug='e12-bulk-root')
    one = Term.objects.create(name='Bulk one', slug='e12-bulk-one', parent=root)
    two = Term.objects.create(name='Bulk two', slug='e12-bulk-two', parent=root)
    response = operator.delete(TERMS + '?parent_id={}'.format(root.pk))
    assert not Term.objects.filter(pk__in=[one.pk, two.pk]).exists(), (
        'the declared leaf scope was not deleted')
    assert Term.objects.filter(pk=root.pk).exists()
    assert response.status_code == 204, response.content[:400]


def test_collection_delete_with_one_affected_leaf_is_refused_atomically(operator):
    root = Term.objects.create(name='Atomic root', slug='e12-atomic-root')
    clean = Term.objects.create(name='Atomic clean', slug='e12-atomic-clean',
                                parent=root)
    affected = Term.objects.create(name='Atomic affected', slug='e12-atomic-affected',
                                   parent=root)
    protected = ProtectedProbe.objects.create(term=affected, note='keep')
    before_terms = term_states()
    response = operator.delete(TERMS + '?parent_id={}'.format(root.pk))
    after_terms = term_states()
    assert after_terms == before_terms, (
        'a partially failed batch delete removed some targets')
    assert ProtectedProbe.objects.filter(pk=protected.pk).exists()
    assert response.status_code == 400, response.content[:400]


def test_collection_delete_unknown_param_never_widens(operator):
    root = Term.objects.create(name='Widen root', slug='e12-widen-root')
    leaf = Term.objects.create(name='Widen leaf', slug='e12-widen-leaf', parent=root)
    before_terms = term_states()
    response = operator.delete(TERMS + '?bogus=1')
    after_terms = term_states()
    assert after_terms == before_terms, 'an unknown parameter widened the DELETE'
    assert response.status_code == 400, response.content[:400]


def test_collection_delete_empty_scope_never_widens(operator):
    root = Term.objects.create(name='Empty root', slug='e12-empty-root')
    leaf = Term.objects.create(name='Empty leaf', slug='e12-empty-leaf', parent=root)
    before_terms = term_states()
    response = operator.delete(TERMS + '?parent_id=')
    after_terms = term_states()
    assert after_terms == before_terms, 'an empty scope widened the DELETE'
    assert response.status_code == 400, response.content[:400]


def test_entity_detail_delete_with_related_characteristic_is_refused(
        operator, entity_types):
    entity = ContractEntity.objects.create(name='E12 effect entity')
    dependent = AdditionalEntityCharacteristicOrMarkModel.objects.create(
        entity=entity, term=entity_types['child'], value='v')
    response = operator.delete('/e12/entities/entities/{}/'.format(entity.pk))
    assert ContractEntity.objects.filter(pk=entity.pk).exists(), (
        'entity DELETE ignored a related characteristic row')
    assert AdditionalEntityCharacteristicOrMarkModel.objects.filter(
        pk=dependent.pk).exists()
    assert response.status_code == 400, response.content[:400]
