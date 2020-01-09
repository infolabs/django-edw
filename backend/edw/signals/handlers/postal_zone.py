# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools
from django.db.models.signals import pre_delete, pre_save

from edw.models.entity import EntityModel
from edw.models.mixins.entity.place import PlaceMixin
from edw.models.postal_zone import PostZoneModel
from edw.signals import make_dispatch_uid

# ==============================================================================
# Find Models with PlaceMixin
# ==============================================================================
_model_with_place_mixin = []

Model = EntityModel.materialized
for clazz in itertools.chain([Model], Model.get_all_subclasses()):
    if issubclass(clazz, PlaceMixin):
        _model_with_place_mixin.append(clazz)


# ==============================================================================
# Postal zone model event handlers
# ==============================================================================

def on_pre_delete_postzone(sender, instance, **kwargs):
    zone_term_id = instance.term.id
    entities_ids = EntityModel.objects.instance_of(*_model_with_place_mixin).filter(terms__id=zone_term_id).values_list(
        'id', flat=True)
    EntityModel.terms.through.objects.filter(entity_id__in=entities_ids, term_id=zone_term_id).delete()


def on_pre_save_postzone(sender, instance, **kwargs):
    if instance.pk is not None:
        try:
            origin = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            if origin.term != instance.term:
                origin_zone_term_id = origin.term.id
                zone_term_id = instance.term.id
                entities_ids = EntityModel.objects.instance_of(*_model_with_place_mixin).filter(
                    terms__id=origin_zone_term_id).values_list('id', flat=True)
                EntityModel.terms.through.objects.filter(
                    entity_id__in=list(entities_ids), term_id=origin_zone_term_id).update(term_id=zone_term_id)


#==============================================================================
# Connect
#==============================================================================
clazz = PostZoneModel.materialized

pre_delete.connect(on_pre_delete_postzone, clazz,
                       dispatch_uid=make_dispatch_uid(pre_delete, on_pre_delete_postzone, clazz))
pre_save.connect(on_pre_save_postzone, clazz,
                  dispatch_uid=make_dispatch_uid(pre_save, on_pre_save_postzone, clazz))