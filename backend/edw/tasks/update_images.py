# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from celery import shared_task

from filer.models import Image

from edw.models.entity import EntityModel
from edw.models.related import EntityImageModel


@shared_task(name='update_entities_images')
def update_entities_images(entities_ids, to_set_images_ids, to_unset_images_ids):
    does_not_exist_entities_ids = []
    does_not_exist_image_field_entities_ids = []
    does_not_exist_images_ids = []

    to_set_images = None
    if to_set_images_ids:
        to_set_images = Image.objects.filter(id__in=to_set_images_ids)
        does_not_exist_images_ids.extend(
            list(
                set(to_set_images_ids) - set([i.id for i in to_set_images])
            )
        )

    if to_set_images:
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
                    for i in to_set_images:
                        EntityImageModel.objects.get_or_create(entity=entity, image=i)
                else:
                    does_not_exist_image_field_entities_ids.append(entity_id)

    to_unset_images = None
    if to_unset_images_ids:
        to_unset_images = Image.objects.filter(id__in=to_unset_images_ids)
        does_not_exist_images_ids.extend(
            list(
                set(to_unset_images_ids) - set([i.id for i in to_unset_images])
            )
        )
    if to_unset_images:
        EntityImageModel.objects.filter(
            entity_id__in=entities_ids, image__in=to_unset_images
        ).delete()

    return {
        'entities_ids': entities_ids,
        'to_set_image_id': to_set_images_ids,
        'to_unset_image_id': to_unset_images_ids,
        'does_not_exist_entities_ids': does_not_exist_entities_ids,
        'does_not_exist_images_ids': does_not_exist_images_ids,
        'does_not_exist_image_field': does_not_exist_image_field_entities_ids
    }
