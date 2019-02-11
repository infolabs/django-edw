# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.db.models import F
from django.db.models.signals import (
    pre_delete,
)

from edw.signals import make_dispatch_uid
from edw.signals.mptt import (
    move_to_done,
    pre_save,
    post_save
)

from edw.models.term import TermModel
from edw.models.data_mart import DataMartModel
from edw.models.entity import EntityModel


def get_children_keys(sender, parent_id):
    key = ":".join([
        sender._meta.object_name.lower(),
        sender.CHILDREN_CACHE_KEY_PATTERN.format(parent_id=parent_id)
        if parent_id is not None else
        "toplvl"
    ])
    return [key, ":".join([key, "actv"])]


def _get_attribute_ancestors_key(sender, id, attribute_mode):
    return ":".join([
        sender._meta.object_name.lower(),
        sender.ANCESTORS_CACHE_KEY_PATTERN.format(id=id, ascending=True, include_self=False),
        sender.ATTRIBUTE_FILTER_CACHE_KEY_PATTERN.format(mode=int(attribute_mode)),
        sender.SELECT_RELATED_CACHE_KEY_PATTERN.format(fields='parent')
    ])

def get_attribute_ancestors_keys(sender, instance):
    return [_get_attribute_ancestors_key(sender, id, attribute_mode) for id in
            instance.get_descendants(include_self=True).values_list('id', flat=True) for attribute_mode in
            (sender.attributes.is_characteristic, sender.attributes.is_mark)]


def get_all_active_attributes_descendants_keys(sender):
    return [sender.ALL_ACTIVE_CHARACTERISTICS_DESCENDANTS_IDS_CACHE_KEY,
            sender.ALL_ACTIVE_MARKS_DESCENDANTS_IDS_CACHE_KEY]


def get_data_mart_all_active_terms_keys():
    return [DataMartModel.ALL_ACTIVE_TERMS_COUNT_CACHE_KEY, DataMartModel.ALL_ACTIVE_TERMS_IDS_CACHE_KEY]


#==============================================================================
# Term model event handlers
#==============================================================================
def invalidate_term_before_save(sender, instance, **kwargs):
    if instance.id is not None:
        try:
            original = sender._default_manager.get(pk=instance.id)
            if original.parent_id != instance.parent_id:
                if original.active != instance.active:
                    TermModel.clear_children_buffer()  # Clear children buffer
                    instance._parent_id_validate = True
                else:
                    keys = get_children_keys(sender, original.parent_id)
                    cache.delete_many(keys)

                keys = get_attribute_ancestors_keys(sender, instance)
                keys.extend(get_all_active_attributes_descendants_keys(sender))
                keys.extend(get_data_mart_all_active_terms_keys())
                cache.delete_many(keys)
            else:
                if original.active != instance.active:
                    keys = get_data_mart_all_active_terms_keys()

                    if instance.active:
                        parent_id_list = list(original.get_family().
                                              exclude(lft=F('rght')-1).values_list('id', flat=True))
                        parent_id_list.append(None)
                    else:
                        parent_id_list = list(original.get_descendants(include_self=True).
                                              exclude(lft=F('rght')-1).values_list('id', flat=True))
                        parent_id_list.append(original.parent_id)

                    for parent_id in parent_id_list:
                        keys.extend(get_children_keys(sender, parent_id))
                    instance._parent_id_validate = True

                    keys.extend(get_all_active_attributes_descendants_keys(sender))
                    instance._all_active_attributes_descendants_validate = True

                    cache.delete_many(keys)

                if original.attributes != instance.attributes or (
                        instance.attributes & (
                            instance.__class__.attributes.is_characteristic | instance.__class__.attributes.is_mark
                        ) and (original.name != instance.name or original.view_class != instance.view_class)):
                    keys = get_attribute_ancestors_keys(sender, instance)
                    if not getattr(instance, '_all_active_attributes_descendants_validate', False):
                        keys.extend(get_all_active_attributes_descendants_keys(sender))
                        instance._all_active_attributes_descendants_validate = True

                    cache.delete_many(keys)

        except sender.DoesNotExist:
            pass


def invalidate_term_after_save(sender, instance, **kwargs):
    if instance.id is not None:
        if not getattr(instance, '_parent_id_validate', False):
            keys = get_children_keys(sender, instance.parent_id)
            cache.delete_many(keys)
    TermModel.clear_decompress_buffer()  # Clear decompress buffer
    cache.delete(TermModel.ALL_ACTIVE_ROOT_IDS_CACHE_KEY) # Clear all active root ids cache
    EntityModel.clear_terms_cache_buffer() # Clear terms ids buffer


def invalidate_term_before_delete(sender, instance, **kwargs):
    keys = get_attribute_ancestors_keys(sender, instance)
    if instance.active:
        keys.extend(get_data_mart_all_active_terms_keys())
        keys.extend(get_all_active_attributes_descendants_keys(sender))
    cache.delete_many(keys)
    invalidate_term_after_save(sender, instance, **kwargs)


def invalidate_term_after_move(sender, instance, target, position, prev_parent, **kwargs):
    prev_parent_id = prev_parent.id if prev_parent is not None else None
    keys = get_children_keys(sender, prev_parent_id)
    if prev_parent_id != instance.parent_id:
        keys.extend(get_attribute_ancestors_keys(sender, instance))
        keys.extend(get_all_active_attributes_descendants_keys(sender))
    cache.delete_many(keys)
    invalidate_term_after_save(sender, instance, **kwargs)


Model = TermModel.materialized
pre_save.connect(invalidate_term_before_save, sender=Model,
                 dispatch_uid=make_dispatch_uid(
                     pre_save,
                     invalidate_term_before_save,
                     Model
                 ))
post_save.connect(invalidate_term_after_save, sender=Model,
                  dispatch_uid=make_dispatch_uid(
                      post_save,
                      invalidate_term_after_save,
                      Model
                  ))
pre_delete.connect(invalidate_term_before_delete, sender=Model,
                   dispatch_uid=make_dispatch_uid(
                       pre_delete,
                       invalidate_term_before_delete,
                       Model
                   ))
move_to_done.connect(invalidate_term_after_move, sender=Model,
                     dispatch_uid=make_dispatch_uid(
                         move_to_done,
                         invalidate_term_after_move,
                         Model
                     ))
