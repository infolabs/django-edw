# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from django.apps import apps
from django.db import transaction
from django.db.models import fields

from edw.models.entity import EntityModel


@shared_task(name='set_boolean_in_entities')
def set_boolean_in_entities(entities_ids, **kwargs):
    model_class = apps.get_model(kwargs['app_label'], kwargs['model_name'])
    opts = model_class._meta

    does_not_exist_entities_ids = []

    entities = list(EntityModel.objects.filter(id__in=entities_ids))
    existing_entities_ids = [i.id for i in entities]
    does_not_exist_entities_ids.extend(
        list(
            set(entities_ids) - set(existing_entities_ids)
        )
    )

    with (transaction.atomic()):
        # get boolean fields list
        bool_fields = [field for field in opts.fields if isinstance(field, fields.BooleanField) and not getattr(
            field, 'protected', False)]
        do_save = False
        for field in bool_fields:
            mode = kwargs[field.name]
            if bool(mode):
                do_save = True
                if mode == 'Toggle':
                    for entity in entities:
                        setattr(entity, field.name, not getattr(entity, field.name))
                else:
                    val = mode == 'True'
                    for entity in entities:
                        setattr(entity, field.name, val)
        if do_save:
            for entity in entities:
                entity.save()

    return {
        'model_class': model_class.__name__,
        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
    }
