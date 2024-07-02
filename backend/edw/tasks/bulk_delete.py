# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel


@shared_task(name='entities_bulk_delete')
def entities_bulk_delete(entities_ids, **kwargs):
    does_not_exist_entities_ids = []

    entities = EntityModel.objects.filter(id__in=entities_ids)
    existing_entities_ids = [i.id for i in entities]
    does_not_exist_entities_ids.extend(
        list(
            set(entities_ids) - set(existing_entities_ids)
        )
    )

    for e in entities:
        e.delete()

    return {
        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
    }