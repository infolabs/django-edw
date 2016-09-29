# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.db.models import F
from django.db.models.signals import (
    pre_delete,
    m2m_changed
)
from django.dispatch import receiver

from edw.signals import make_dispatch_uid
from edw.signals.mptt import (
    move_to_done,
    pre_save,
    post_save
)

from edw.models.data_mart import DataMartModel
from edw.models.term import TermModel


def get_children_keys(sender, parent_id):
    key = ":".join([
        sender._meta.object_name.lower(),
        sender.CHILDREN_CACHE_KEY_PATTERN.format(parent_id=parent_id)
        if parent_id is not None else
        "toplvl"
    ])
    return [key, ":".join([key, "actv"])]


def get_data_mart_all_active_terms_keys():
    return [DataMartModel.ALL_ACTIVE_TERMS_COUNT_CACHE_KEY, DataMartModel.ALL_ACTIVE_TERMS_IDS_CACHE_KEY]


#==============================================================================
# DataMart model event handlers
#==============================================================================
Model = DataMartModel.terms.through
@receiver(m2m_changed, sender=Model, dispatch_uid=make_dispatch_uid(
    m2m_changed, 'invalidate_after_terms_set_changed', Model))
def invalidate_after_terms_set_changed(sender, instance, **kwargs):
    if getattr(instance, "_during_terms_validation", False):
        return
    pk_set = kwargs.pop('pk_set', None)
    action = kwargs.pop('action', None)

    if action in ["pre_remove", "pre_add"]:
        if instance.system_flags.change_terms_restriction:
            # disable updating terms set on change restriction
            pk_set.clear()
            return

    if action == "pre_add":
        # normalize terms set
        origin_pk_set = set(instance.terms.values_list('id', flat=True))
        tree = TermModel.decompress(origin_pk_set | pk_set, fix_it=True)
        normal_pk_set = set([x.term.id for x in tree.values() if x.is_leaf])
        # pk set to add
        pk_set_difference = normal_pk_set - origin_pk_set
        pk_set.clear()
        pk_set.update(pk_set_difference)
        # pk set to remove
        pk_set_difference = origin_pk_set - normal_pk_set
        if pk_set_difference:
            instance._during_terms_validation = True
            instance.terms.remove(*list(pk_set_difference))
            del instance._during_terms_validation

    elif action in ['post_add', 'post_remove']:
        # clear cache
        keys = get_data_mart_all_active_terms_keys()
        cache.delete_many(keys)


def invalidate_data_mart_before_save(sender, instance, **kwargs):
    if instance.id is not None:
        try:
            original = sender._default_manager.get(pk=instance.id)
            if original.parent_id != instance.parent_id:
                if original.active != instance.active:
                    DataMartModel.clear_children_buffer()  # Clear children buffer
                    instance._parent_id_validate = True
                else:
                    keys = get_children_keys(sender, original.parent_id)
                    cache.delete_many(keys)
            else:
                if original.active != instance.active:
                    if instance.active:
                        parent_id_list = list(original.get_family().
                                              exclude(lft=F('rght')-1).values_list('id', flat=True))
                        parent_id_list.append(None)
                    else:
                        parent_id_list = list(original.get_descendants(include_self=True).
                                              exclude(lft=F('rght')-1).values_list('id', flat=True))
                        parent_id_list.append(original.parent_id)
                    keys = []
                    for parent_id in parent_id_list:
                        keys.extend(get_children_keys(sender, parent_id))
                    cache.delete_many(keys)
                    instance._parent_id_validate = True
        except sender.DoesNotExist:
            pass


def invalidate_data_mart_after_save(sender, instance, **kwargs):
    if instance.id is not None and not getattr(instance, '_parent_id_validate', False) :
        keys = get_children_keys(sender, instance.parent_id)
        cache.delete_many(keys)


def invalidate_data_mart_before_delete(sender, instance, **kwargs):
    keys = get_data_mart_all_active_terms_keys()
    cache.delete_many(keys)

    invalidate_data_mart_after_save(sender, instance, **kwargs)


def invalidate_data_mart_after_move(sender, instance, target, position, prev_parent, **kwargs):
    keys = get_children_keys(sender, prev_parent.id if prev_parent is not None else None)
    cache.delete_many(keys)

    invalidate_data_mart_after_save(sender, instance, **kwargs)


Model = DataMartModel.materialized
for clazz in [Model] + Model.__subclasses__():
    pre_save.connect(invalidate_data_mart_before_save, sender=clazz,
                     dispatch_uid=make_dispatch_uid(
                         pre_save,
                         invalidate_data_mart_before_save,
                         clazz
                     ))
    post_save.connect(invalidate_data_mart_after_save, sender=clazz,
                      dispatch_uid=make_dispatch_uid(
                          post_save,
                          invalidate_data_mart_after_save,
                          clazz
                      ))
    pre_delete.connect(invalidate_data_mart_before_delete, sender=clazz,
                       dispatch_uid=make_dispatch_uid(
                           pre_delete,
                           invalidate_data_mart_before_delete,
                           clazz
                       ))
    move_to_done.connect(invalidate_data_mart_after_move, sender=clazz,
                         dispatch_uid=make_dispatch_uid(
                             move_to_done,
                             invalidate_data_mart_after_move,
                             clazz
                         ))
