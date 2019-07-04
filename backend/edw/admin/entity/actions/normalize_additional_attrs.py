#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.entity.actions.base_entity_action import base_entity_action
from edw.tasks import normalize_entities_additional_attrs


def normalize_additional_attrs(modeladmin, request, queryset):
    """
    ENG: Normalize additional attributes
    RUS: Нормализует дополнительные атрибуты
    """
    CHUNK_SIZE = getattr(settings, 'EDW_NORMALIZE_ADDITIONAL_ATTRS_ACTION_CHUNK_SIZE', 100)

    title = _("Normalize additional attributes")

    return base_entity_action(
        modeladmin, request, queryset, 'normalize_additional_attrs',
        normalize_entities_additional_attrs, title, CHUNK_SIZE
    )

normalize_additional_attrs.short_description = _("Normalize additional attributes for selected %(verbose_name_plural)s")
