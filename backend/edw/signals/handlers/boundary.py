# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import itertools

from django.core.cache import cache
from django.db.models.signals import pre_delete, pre_save

from edw.models.entity import EntityModel
from edw.models.mixins.entity.place import PlaceMixin
from edw.models.boundary import BoundaryModel
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
# Boundary model event handlers
# ==============================================================================

def clear_boundary_polygons_cache(instance):
    key = instance.POLYGONS_CACHE_KEY_PATTERN.format(instance.id)
    cache.delete(key)


def on_pre_delete_boundary(sender, instance, **kwargs):
    clear_boundary_polygons_cache(instance)


def on_pre_save_boundary(sender, instance, **kwargs):
    if instance.pk is not None:
        try:
            origin = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            pass
        else:
            if origin.term != instance.term:
                origin_boundary_term_id = origin.term.id
                boundary_term_id = instance.term.id
                entities_ids = EntityModel.objects.instance_of(*_model_with_place_mixin).filter(
                    terms__id=origin_boundary_term_id).values_list('id', flat=True)
                EntityModel.terms.through.objects.filter(
                    entity_id__in=list(entities_ids), term_id=origin_boundary_term_id).update(term_id=boundary_term_id)

        clear_boundary_polygons_cache(instance)


#==============================================================================
# Connect
#==============================================================================
clazz = BoundaryModel.materialized

pre_delete.connect(on_pre_delete_boundary, clazz,
                       dispatch_uid=make_dispatch_uid(pre_delete, on_pre_delete_boundary, clazz))
pre_save.connect(on_pre_save_boundary, clazz,
                  dispatch_uid=make_dispatch_uid(pre_save, on_pre_save_boundary, clazz))
