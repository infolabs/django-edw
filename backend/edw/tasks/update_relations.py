# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import simplejson as json

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.term import TermModel
from edw.models.related import EntityRelationModel


@shared_task(name='update_entities_relations')
def update_entities_relations(entities_ids, to_set_relation_term_id, to_set_target_ids,
                              to_unset_relation_term_id, to_unset_target_ids):
    does_not_exist_entities_ids = []
    does_not_exist_relations_terms_ids = []
    exist_to_set_targets_ids = []
    exist_to_unset_targets_ids = []

    to_set_relation_term = None
    if to_set_relation_term_id is not None:
        try:
            to_set_relation_term = TermModel.objects.attribute_is_relation().get(id=to_set_relation_term_id)
        except TermModel.DoesNotExist:
            does_not_exist_relations_terms_ids.append(to_set_relation_term_id)
    if to_set_relation_term is not None:
        if to_set_target_ids:
            exist_to_set_targets_ids = EntityModel.objects.filter(id__in=to_set_target_ids).values_list('id', flat=True)
            for to_set_target_id in exist_to_set_targets_ids:
                for entity_id in entities_ids:
                    try:
                        entity = EntityModel.objects.get(id=entity_id)
                    except EntityModel.DoesNotExist:
                        does_not_exist_entities_ids.append(entity_id)
                    else:
                        EntityRelationModel.objects.get_or_create(from_entity=entity, to_entity_id=to_set_target_id,
                                                                  term=to_set_relation_term)

    to_unset_relation_term = None
    if to_unset_relation_term_id is not None:
        try:
            to_unset_relation_term = TermModel.objects.attribute_is_relation().get(
                id=to_unset_relation_term_id)
        except TermModel.DoesNotExist:
            does_not_exist_relations_terms_ids.append(to_unset_relation_term_id)
    if to_unset_relation_term is not None:
        if to_unset_target_ids is not None:
            exist_to_unset_targets_ids = EntityModel.objects.filter(
                id__in=to_unset_target_ids).values_list('id', flat=True)
            if exist_to_unset_targets_ids:
                EntityRelationModel.objects.filter(to_entity_id__in=exist_to_unset_targets_ids,
                                                   from_entity_id__in=entities_ids,
                                                   term=to_unset_relation_term).delete()

    return json.dumps({
        'entities_ids': entities_ids,
        'to_set_relation_term_id': to_set_relation_term_id,
        'to_set_target_ids': to_set_target_ids,
        'to_unset_relation_term_id': to_unset_relation_term_id,
        'to_unset_target_ids': to_unset_target_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'exist_to_set_targets_ids': exist_to_set_targets_ids,
        'exist_to_unset_targets_ids': exist_to_unset_targets_ids,
        'does_not_exist_relation_term_ids': does_not_exist_relations_terms_ids
    })