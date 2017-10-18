# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools

from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from edw.models.defaults.postal_zone import PostalZone
from edw.models.entity import EntityModel
from edw.signals import make_dispatch_uid


ModelWithPlaceMinix = list()

Model = EntityModel.materialized
for clazz in itertools.chain([Model], Model.get_all_subclasses()):
    if getattr(clazz, 'PlaceMixin', None) is not None:
        ModelWithPlaceMinix.append(clazz)

@receiver(pre_delete, sender=PostalZone, dispatch_uid=make_dispatch_uid(
    pre_delete, 'on_pre_delete_postzone', PostalZone))
def on_pre_delete_postzone(sender, instance, **kwargs):
    zone_term = instance.term
    for model in ModelWithPlaceMinix:
        for inst in model.objects.filter(terms=zone_term):
            inst.terms.remove(zone_term)