# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db.models.signals import (
    m2m_changed,
    pre_delete,
    post_save
)
from django.dispatch import receiver

from edw.models.entity import EntityModel
from edw.models.term import TermModel
from edw.rest.serializers.entity import EntityCommonSerializer
from edw.signals import make_dispatch_uid
from edw.signals.entity import external_add_terms, external_remove_terms


def get_HTML_snippets_keys(sender):
    app_label = sender._meta.app_label.lower()
    languages = getattr(settings, 'LANGUAGES', ())
    return [EntityCommonSerializer.HTML_SNIPPET_CACHE_KEY_PATTERN.format(
        sender.id, app_label, label, sender.entity_model, 'media', language[0])
        for label in ('summary', 'detail') for language in languages]


# ==============================================================================
# Entity model event handlers
# ==============================================================================

# invalidate after terms set changed
Model = EntityModel.terms.through


@receiver(m2m_changed, sender=Model, dispatch_uid=make_dispatch_uid(
    m2m_changed, 'invalidate_after_terms_set_changed', Model))
def invalidate_after_terms_set_changed(sender, instance, **kwargs):
    if getattr(instance, "_during_terms_normalization", False):
        return

    action = kwargs.pop('action', None)
    if action in ["pre_remove", "pre_add"]:
        valid_pk_set = getattr(instance, "_valid_pk_set", None)
        if valid_pk_set is None:
            valid_pk_set = set()
            setattr(instance, "_valid_pk_set", valid_pk_set)

        pk_set = kwargs.pop('pk_set')

        if getattr(instance, "_during_terms_validation", False):
            valid_pk_set.update(pk_set)
            return

        normal_pk_set = set(TermModel.objects.filter(pk__in=pk_set).exclude(
            system_flags=TermModel.system_flags.external_tagging_restriction).order_by().values_list('id', flat=True))
        normal_pk_set.difference_update(valid_pk_set)

        pk_set.clear()
        pk_set.update(normal_pk_set)

        if action == "pre_add":
            # normalize terms set
            origin_pk_set = set(instance.terms.values_list('id', flat=True))
            tree = TermModel.decompress(origin_pk_set | pk_set, fix_it=False)
            normal_pk_set = set([x.term.id for x in tree.values() if x.is_leaf])
            # pk set to add
            pk_set_difference = normal_pk_set - origin_pk_set
            pk_set.clear()
            pk_set.update(pk_set_difference)
            # pk set to remove
            pk_set_difference = origin_pk_set - normal_pk_set
            if pk_set_difference:
                instance._during_terms_normalization = True
                instance.terms.remove(*list(pk_set_difference))
                del instance._during_terms_normalization

            if pk_set:
                external_add_terms.send(sender=instance.__class__, instance=instance, pk_set=pk_set)
        else:
            if pk_set:
                external_remove_terms.send(sender=instance.__class__, instance=instance, pk_set=pk_set)


# invalidate after entity changed
def invalidate_entity_after_save(sender, instance, **kwargs):
    # Clear terms ids buffer
    EntityModel.clear_terms_cache_buffer()

    # Clear HTML snippets
    keys = get_HTML_snippets_keys(instance)

    # Clear Data Mart cache
    keys.append(instance.get_data_mart_cache_key())

    cache.delete_many(keys)


def invalidate_entity_before_delete(sender, instance, **kwargs):
    invalidate_entity_after_save(sender, instance, **kwargs)


# ==============================================================================
# Connect EntityImageModel, EntityFileModel
# &
# invalidate after images and file set changed
# ==============================================================================

def invalidate_entity_after_file_save(sender, instance, **kwargs):
    # Clear HTML snippets
    keys = get_HTML_snippets_keys(instance.entity)
    cache.delete_many(keys)


def invalidate_entity_before_file_delete(sender, instance, **kwargs):
    invalidate_entity_after_file_save(sender, instance, **kwargs)


subclasses = []

try:
    from edw.models.related.entity_image import EntityImageModel
    EntityImageModel()  # Test pass if model materialized
except (ImproperlyConfigured, ImportError, RuntimeError):
    pass
else:
    subclasses.append(EntityImageModel.materialized)

try:
    from edw.models.related.entity_file import EntityFileModel
    EntityFileModel()  # Test pass if model materialized
except (ImproperlyConfigured, ImportError, RuntimeError):
    pass
else:
    subclasses.append(EntityFileModel.materialized)

for clazz in subclasses:
    post_save.connect(invalidate_entity_after_file_save, clazz,
                      dispatch_uid=make_dispatch_uid(post_save, invalidate_entity_after_file_save, clazz))
    pre_delete.connect(invalidate_entity_before_file_delete, clazz,
                       dispatch_uid=make_dispatch_uid(pre_delete, invalidate_entity_before_file_delete, clazz))


# ==============================================================================
# Connect all subclasses of base content item too
# &
# Term model validation
# ==============================================================================
# init cache for .entity_model
EntityModel._content_type_cache = {}

# init cache for .validate_term_model()
EntityModel._validate_term_model_cache = {}

Model = EntityModel.materialized

subclasses = list(Model.get_all_subclasses())
subclasses.append(Model)
subclasses.reverse()
for clazz in subclasses:
    pre_delete.connect(invalidate_entity_before_delete, clazz,
                       dispatch_uid=make_dispatch_uid(pre_delete, invalidate_entity_before_delete, clazz))
    post_save.connect(invalidate_entity_after_save, clazz,
                      dispatch_uid=make_dispatch_uid(post_save, invalidate_entity_after_save, clazz))

    cls_key = clazz.__name__.lower()

    # Устанавливаем таймаут для валидации терминов
    key = 'vldt:{cls}:tr'.format(cls=cls_key)
    is_valid = cache.get(key, False)
    if not is_valid:
        cache.set(key, True, clazz.VALIDATE_TERM_MODEL_CACHE_TIMEOUT)
        clazz.validate_term_model()

    # Устанавливаем таймаут для валидации витрин данных
    key = 'vldt:{cls}:dm'.format(cls=cls_key)
    is_valid = cache.get(key, False)
    if not is_valid:
        cache.set(key, True, clazz.VALIDATE_DATA_MART_MODEL_CACHE_TIMEOUT)
        clazz.validate_data_mart_model()

# delete cache for .validate_term_model()
del EntityModel._validate_term_model_cache
