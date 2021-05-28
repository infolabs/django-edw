# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from django.apps import apps
from django.contrib.contenttypes.models import ContentType


@shared_task(name='extract_ner_data')
def extract_ner_data(**kwargs):
    obj_id = kwargs.get('obj_id', None)
    obj_model = kwargs.get('obj_model', None)
    result = {}
    if obj_id is not None and obj_model is not None:
        content_type = ContentType.objects.get(model=obj_model)
        model = apps.get_model(content_type.app_label, obj_model)
        obj = model.objects.get(id=obj_id)
        result = obj.extract_ner()
    return result
