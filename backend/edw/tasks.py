# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.term import TermModel
from edw.models.related import EntityRelationModel


@shared_task
def update_entities_terms(entities_ids, to_set_terms_ids, to_unset_terms_ids):
    does_not_exist = []

    for entity_id in entities_ids:
        try:
            entity = EntityModel.objects.get(id=entity_id)
            entity.terms.add(*to_set_terms_ids)
            entity.terms.remove(*to_unset_terms_ids)

        except EntityModel.DoesNotExist:
            does_not_exist.append(entity_id)

    return {
        'entities_ids': entities_ids,
        'to_set_terms_ids': to_set_terms_ids,
        'to_unset_terms_ids': to_unset_terms_ids,
        'does_not_exist_entities_ids': does_not_exist
    }


@shared_task
def update_entities_relations(entities_ids, relation_term_id, to_set_target_id, to_unset_target_id):
    does_not_exist_entities_ids = []
    does_not_exist_targets_ids = []
    does_not_exist_relation_term_ids = []

    relation_term = None
    try:
        relation_term = TermModel.objects.attribute_is_relation().get(id=relation_term_id)
    except TermModel.DoesNotExist:
        does_not_exist_relation_term_ids.append(relation_term_id)

    if relation_term is not None:
        to_set_target = None
        if to_set_target_id is not None:
            try:
                to_set_target = EntityModel.objects.get(id=to_set_target_id)
            except EntityModel.DoesNotExist:
                does_not_exist_targets_ids.append(to_set_target_id)

            if to_set_target:
                for entity_id in entities_ids:
                    try:
                        entity = EntityModel.objects.get(id=entity_id)
                        EntityRelationModel.objects.get_or_create(from_entity=entity, to_entity=to_set_target,
                                                                      term=relation_term)
                    except EntityModel.DoesNotExist:
                        does_not_exist_entities_ids.append(entity_id)

        to_unset_target = None
        if to_unset_target_id is not None:
            try:
                to_unset_target = EntityModel.objects.get(id=to_unset_target_id)
            except EntityModel.DoesNotExist:
                does_not_exist_targets_ids.append(to_unset_target_id)

            if to_unset_target:
                EntityRelationModel.objects.filter(to_entity=to_unset_target, from_entity__id__in=entities_ids,
                                                   term=relation_term).delete()
    return {
        'entities_ids': entities_ids,
        'relation_term_id': relation_term_id,
        'to_set_target_id': to_set_target_id,
        'to_unset_target_id': to_unset_target_id,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'does_not_exist_targets_ids': does_not_exist_targets_ids,
        'does_not_exist_relation_term_ids': does_not_exist_relation_term_ids
    }
