# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel


@shared_task(name='update_entities_active')
def update_entities_active(entities_ids, to_set_active):
    does_not_exist_entities_ids = []

    entities = EntityModel.objects.filter(id__in=entities_ids)
    existing_entities_ids =  [i.id for i in entities]
    does_not_exist_entities_ids.extend(
        list(
            set(entities_ids) - set(existing_entities_ids)
        )
    )
    for e in entities:
        e.active = to_set_active
        e.save()

    return {
        'entities_ids': entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
    }
