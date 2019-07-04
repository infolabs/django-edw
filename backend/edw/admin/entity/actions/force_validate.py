#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.entity.actions.base_entity_action import base_entity_action
from edw.tasks import entities_force_validate


def force_validate(modeladmin, request, queryset):
    """
    ENG: Save multiple entities with force validate terms
    RUS: Сохраняет объекты с принудительной проверкой терминов
    """
    CHUNK_SIZE = getattr(settings, 'EDW_ENTITIES_FORCE_VALIDATE_ACTION_CHUNK_SIZE', 100)

    title = _("Save multiple entities with force validate terms")

    return base_entity_action(
        modeladmin, request, queryset, 'force_validate', entities_force_validate, title, CHUNK_SIZE
    )

force_validate.short_description = _("Save with force validate terms for selected %(verbose_name_plural)s")
