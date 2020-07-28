# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from django.apps import apps
from django.conf import settings


@shared_task(name='send_notification')
def send_notification(model_name, instance_id, source, target):
    res = {
        'model_name': model_name,
        'instance_id': instance_id,
        'source': source,
        'target': target,
    }
    model = apps.get_model(settings.EDW_APP_LABEL, model_name)
    instance = model.objects.filter(id=instance_id).first()
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
