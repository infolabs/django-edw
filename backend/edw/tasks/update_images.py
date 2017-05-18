# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from filer.models import Image

from edw.models.entity import EntityModel
from edw.models.related import EntityImageModel


@shared_task(name='update_entities_images')
def update_entities_images(entities_ids, to_set_image_id, to_unset_image_id):
    does_not_exist_entities_ids = []
    does_not_exist_image_field_entities_ids = []
    does_not_exist_images_ids = []

    to_set_image = None
    if to_set_image_id is not None:
        try:
            to_set_image = Image.objects.get(id=to_set_image_id)
        except Image.DoesNotExist:
            does_not_exist_images_ids.append(to_set_image_id)

    if to_set_image:
        for entity_id in entities_ids:
            try:
                entity = EntityModel.objects.get(id=entity_id)
            except EntityModel.DoesNotExist:
                does_not_exist_entities_ids.append(entity_id)
            else:
                image_relation_exist = False
                fields = entity._meta.get_fields()
                for f in fields:
                    rel = getattr(f, "rel", False)
                    if rel and issubclass(rel.model, Image):
                        image_relation_exist = True
                        break
                if image_relation_exist:
                    if to_set_image_id:
                        EntityImageModel.objects.get_or_create(entity=entity, image=to_set_image)
                else:
                    does_not_exist_image_field_entities_ids.append(entity_id)

    to_unset_image = None
    if to_unset_image_id is not None:
        try:
            to_unset_image = Image.objects.get(id=to_unset_image_id)
        except Image.DoesNotExist:
            does_not_exist_images_ids.append(to_unset_image_id)

    if to_unset_image:
        EntityImageModel.objects.filter(entity_id__in=entities_ids, image=to_unset_image).delete()

    return {
        'entities_ids': entities_ids,
        'to_set_image_id': to_set_image_id,
        'to_unset_image_id': to_unset_image_id,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'does_not_exist_images_ids': does_not_exist_images_ids,
        'does_not_exist_image_field': does_not_exist_image_field_entities_ids
    }
