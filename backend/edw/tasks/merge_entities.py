# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from django.apps import apps
from django.db.models import fields

from edw.models.entity import EntityModel


@shared_task(name='merge_entities')
def merge_entities(entities_ids, **kwargs):
    model_class = apps.get_model(kwargs['app_label'], kwargs['model_name'])
    opts = model_class._meta

    does_not_exist_entities_ids = []

    order = 'id' if kwargs['order'] else '-id'
    entities = list(EntityModel.objects.filter(id__in=entities_ids).order_by(order))
    existing_entities_ids = [i.id for i in entities]
    does_not_exist_entities_ids.extend(
        list(
            set(entities_ids) - set(existing_entities_ids)
        )
    )

    updated_entity_id = None
    deleted_entities_ids = []

    common_terms_ids = set()

    if len(entities) > 1:
        head, tail = entities[0], entities[1:]

        # merge strings
        joiner = kwargs['joiner']
        char_fields = [field for field in opts.fields if isinstance(field, fields.CharField) and not getattr(
            field, 'protected', False) and kwargs.get(field.name, False)]
        for field in char_fields:
            value = joiner.join([getattr(x, field.name) for x in entities])[:field.max_length]
            setattr(head, field.name, value)

        # merge common terms
        if kwargs['terms']:
            [common_terms_ids.update(x.common_terms_ids) for x in tail]
            head.terms.add(*common_terms_ids)

        # merge relations...

        # merge characteristics and marks...

        # merge external foreign key...

        # save head
        updated_entity_id = head.id
        head.save()

        # delete tail
        deleted_entities_ids = [x.id for x in tail]
        EntityModel.objects.filter(id__in=deleted_entities_ids).delete()

    return {
        'common_terms_ids': list(common_terms_ids),

        'model_class': model_class.__name__,

        'updated_entity_id': updated_entity_id,
        'deleted_entities_ids': deleted_entities_ids,

        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
    }
