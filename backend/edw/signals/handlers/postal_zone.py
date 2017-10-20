# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools

from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from edw.models.defaults.postal_zone import PostalZone
from edw.models.entity import EntityModel
from edw.signals import make_dispatch_uid


ModelWithPlaceMinix = []

Model = EntityModel.materialized
for clazz in itertools.chain([Model], Model.get_all_subclasses()):
    if getattr(clazz, 'PlaceMixin', None) is not None:
        ModelWithPlaceMinix.append(clazz)

@receiver(pre_delete, sender=PostalZone, dispatch_uid=make_dispatch_uid(
    pre_delete, 'on_pre_delete_postzone', PostalZone))
def on_pre_delete_postzone(sender, instance, **kwargs):
    zone_term_id = instance.term.id
    entities_ids = EntityModel.objects.instance_of(*ModelWithPlaceMinix).filter(terms__id=zone_term_id).values_list(
        'id', flat=True)
    EntityModel.terms.through.objects.filter(entity_id__in=entities_ids, term_id=zone_term_id).delete()

@receiver(pre_save, sender=PostalZone, dispatch_uid=make_dispatch_uid(
    pre_save, 'on_pre_save_postzone', PostalZone))
def on_pre_save_postzone(sender, instance, **kwargs):
    if instance.pk is not None:
        origin = PostalZone.objects.get(pk=instance.pk)
        if origin.term != instance.term:
            origin_zone_term_id = origin.term.id
            zone_term = instance.term
            entities_ids = EntityModel.objects.instance_of(*ModelWithPlaceMinix).filter(
                terms__id=origin_zone_term_id).values_list('id', flat=True)
            terms = EntityModel.terms.through.objects.filter(entity_id__in=entities_ids, term_id=origin_zone_term_id)
            for term in terms:
                term.term = zone_term
                term.save()