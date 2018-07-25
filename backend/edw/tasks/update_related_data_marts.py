# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.models.related import EntityRelatedDataMartModel


@shared_task(name='update_entities_related_data_marts')
def update_entities_related_data_marts(entities_ids, to_set_datamart_ids, to_unset_datamart_ids):
    does_not_exist_entities_ids = []
    does_not_exist_datamarts_ids = []

    if to_set_datamart_ids:
        to_set_related_data_marts = DataMartModel.objects.filter(id__in=to_set_datamart_ids)
        does_not_exist_datamarts_ids.extend(
            list(
                set(to_set_datamart_ids) - set([i.id for i in to_set_related_data_marts])
            )
        )
        if len(to_set_related_data_marts):
            for entity_id in entities_ids:
                try:
                    entity = EntityModel.objects.get(id=entity_id)
                except EntityModel.DoesNotExist:
                    does_not_exist_entities_ids.append(entity_id)
                else:
                    for data_mart in to_set_related_data_marts:
                        EntityRelatedDataMartModel.objects.get_or_create(
                            entity=entity, data_mart=data_mart
                        )

    if to_unset_datamart_ids:
        to_unset_related_data_marts = DataMartModel.objects.filter(id__in=to_unset_datamart_ids)
        does_not_exist_datamarts_ids.extend(
            list(
                set(to_unset_datamart_ids) - set([i.id for i in to_unset_related_data_marts])
            )
        )
        if len(to_unset_related_data_marts):
            EntityRelatedDataMartModel.objects.filter(
                entity__id__in=entities_ids,
                data_mart__in=to_unset_related_data_marts
            ).delete()

    return {
        'entities_ids': entities_ids,
        'to_set_datamart_ids': to_set_datamart_ids,
        'to_unset_datamart_ids': to_unset_datamart_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'does_not_exist_datamarts_ids': does_not_exist_datamarts_ids
    }
