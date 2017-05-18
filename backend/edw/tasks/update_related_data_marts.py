# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.models.term import TermModel
from edw.models.related import EntityRelatedDataMartModel


@shared_task(name='update_entities_related_data_marts')
def update_entities_related_data_marts(entities_ids, to_set_datamart_id, to_unset_datamart_id):

    does_not_exist_entities_ids = []
    does_not_exist_datamarts_ids = []

    to_set_relation_data_mart = None
    if to_set_datamart_id is not None:
        try:
            to_set_relation_data_mart = DataMartModel.objects.get(id=to_set_datamart_id)
        except TermModel.DoesNotExist:
            does_not_exist_datamarts_ids.append(to_set_datamart_id)
    if to_set_relation_data_mart is not None:
        for entity_id in entities_ids:
            try:
                entity = EntityModel.objects.get(id=entity_id)
                EntityRelatedDataMartModel.objects.get_or_create(entity=entity, data_mart=to_set_relation_data_mart)
            except EntityModel.DoesNotExist:
                does_not_exist_entities_ids.append(entity_id)

    # to_unset_relation_term = None
    # if to_unset_relation_term_id is not None:
    #     try:
    #         to_unset_relation_term = TermModel.objects.attribute_is_relation().get(
    #             id=to_unset_relation_term_id)
    #     except TermModel.DoesNotExist:
    #         does_not_exist_relations_terms_ids.append(to_unset_relation_term_id)
    # if to_unset_relation_term is not None:
    #     if to_unset_target_id is not None:
    #         to_unset_target = None
    #         try:
    #             to_unset_target = EntityModel.objects.get(id=to_unset_target_id)
    #         except EntityModel.DoesNotExist:
    #             does_not_exist_targets_ids.append(to_unset_target_id)
    #
    #         if to_unset_target:
    #             EntityRelationModel.objects.filter(to_entity=to_unset_target, from_entity__id__in=entities_ids,
    #                                                term=to_unset_relation_term).delete()

    return {
        'entities_ids': entities_ids,
        'to_set_datamart_id': to_set_datamart_id,
        'to_unset_datamart_id': to_unset_datamart_id,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'does_not_exist_datamarts_ids': does_not_exist_datamarts_ids
    }