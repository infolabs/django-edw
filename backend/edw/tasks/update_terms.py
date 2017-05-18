# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel


@shared_task(name='update_entities_terms')
def update_entities_terms(entities_ids, to_set_terms_ids, to_unset_terms_ids):
    does_not_exist = []

    for entity_id in entities_ids:
        try:
            entity = EntityModel.objects.get(id=entity_id)
        except EntityModel.DoesNotExist:
            does_not_exist.append(entity_id)
        else:
            entity.terms.add(*to_set_terms_ids)
            entity.terms.remove(*to_unset_terms_ids)

    return {
        'entities_ids': entities_ids,
        'to_set_terms_ids': to_set_terms_ids,
        'to_unset_terms_ids': to_unset_terms_ids,
        'does_not_exist_entities_ids': does_not_exist
    }