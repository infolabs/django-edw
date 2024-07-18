# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from django.apps import apps
from django.db import transaction

from django.db.models.fields.related import ForeignKey

from edw.models.entity import EntityModel


@shared_task(name='set_foreign_key_in_entities')
def set_foreign_key_in_entities(entities_ids, **kwargs):
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
        # get foreign keys fields list
        fk_fields = [x for x in opts.fields if (isinstance(x, ForeignKey) and x.editable and
                                                      x.get_internal_type() == 'ForeignKey')]
        do_save = False
        for field in fk_fields:
            pk = kwargs.get(field.name, None)
            if pk is not None:
                do_save = True
                for entity in entities:
                    setattr(entity, f"{field.name}_id", pk)

        if do_save:
            for entity in entities:
                entity.save()

    return {
        'model_class': model_class.__name__,
        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
    }
