# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from edw.models.entity import EntityModel


@shared_task(name='send_notification')
def send_notification(entity_id, source, target):
    res = {
        'entity': entity_id,
        'source': source,
        'target': target,
    }
    instance = EntityModel.objects.filter(id=entity_id).first()
    if instance:
        instance.send_notification(source, target)
        res.update({
            'status': 'success'
        })
    else:
        res.update({
            'status': 'error'
        })
    return res