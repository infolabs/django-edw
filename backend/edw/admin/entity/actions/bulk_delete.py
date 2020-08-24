# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.entity.actions.base_entity_action import base_entity_action
from edw.tasks import entities_bulk_delete


def bulk_delete(modeladmin, request, queryset):
    """
    ENG: Delete multiple entities
    RUS: Массовое удаление объектов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_ENTITIES_BULK_DELETE_ACTION_CHUNK_SIZE', 100)

    title = _("Delete multiple entities with bulk delete")

    return base_entity_action(
        modeladmin, request, queryset, 'bulk_delete', entities_bulk_delete, title, CHUNK_SIZE
    )


bulk_delete.short_description = _("Delete with bulk delete for selected %(verbose_name_plural)s")
