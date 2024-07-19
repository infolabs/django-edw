# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from django.apps import apps
from django.db import transaction
from django.db.models import fields
from django.db.models.fields.related import ManyToManyRel

from edw.models.entity import EntityModel
from edw.models.related import AdditionalEntityCharacteristicOrMarkModel, EntityRelatedDataMartModel


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

    if len(entities) > 1:
        head, tail = entities[0], entities[1:]

        with (transaction.atomic()):
            # merge strings
            joiner = kwargs['joiner']
            char_fields = [field for field in opts.fields if isinstance(field, fields.CharField) and not getattr(
                field, 'protected', False) and kwargs.get(field.name, False)]
            for field in char_fields:
                value = joiner.join([value for x in entities if (value := getattr(x, field.name)) is not None])[:field.max_length]
                setattr(head, field.name, value)

            # merge common terms
            if kwargs['terms']:
                common_terms_ids = set()
                [common_terms_ids.update(x.common_terms_ids) for x in tail]
                head.terms.add(*common_terms_ids)

            # get objects ids for merging
            pks = set([x.id for x in tail])

            # merge characteristics or marks
            if kwargs['characteristics_or_marks']:
                AdditionalEntityCharacteristicOrMarkModel.objects.filter(entity__in=pks).update(entity=head.id)

            # merge related datamarts
            if kwargs['related_datamarts']:
                EntityRelatedDataMartModel.objects.filter(entity__in=pks).update(entity=head.id)

            # update related objects
            for related_object in opts.related_objects:
                if not related_object.remote_field.name.startswith('_'):
                    field_name = f"{related_object.related_model._meta.model_name}__{related_object.remote_field.name}"
                    if kwargs.get(field_name, False):
                        if isinstance(related_object, ManyToManyRel):
                            related_object.through.objects.filter(
                                **{f"{related_object.remote_field.related_model._meta.model_name}__in": pks}).update(
                                **{related_object.remote_field.related_model._meta.model_name: head.id})
                        else:
                            related_object.related_model.objects.filter(
                                **{f"{related_object.remote_field.name}__in": pks}).update(
                                **{related_object.remote_field.name: head.id})

            # save head
            updated_entity_id = head.id
            head.save()

            # delete tail
            deleted_entities_ids = [x.id for x in tail]
            EntityModel.objects.filter(id__in=deleted_entities_ids).delete()

    return {
        'model_class': model_class.__name__,
        'updated_entity_id': updated_entity_id,
        'deleted_entities_ids': deleted_entities_ids,
        'existing_entities_ids': existing_entities_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
    }
