# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import objects_action
from edw.tasks import set_foreign_key_in_entities
from edw.admin.entity.forms.set_foreign_key import SetForeignKeyInEntitiesActionAdminForm


def set_foreign_key(modeladmin, request, queryset):
    """
    ENG: Set foreign key in multiple entities

    """
    CHUNK_SIZE = getattr(settings, 'EDW_SET_FOREIGN_KEY_IN_ENTITIES_ACTION_CHUNK_SIZE', 100)

    title = _("Set foreign keys in multiple entities")

    return objects_action(
        modeladmin, request, queryset, 'set_foreign_key', set_foreign_key_in_entities, title, CHUNK_SIZE,
        admin_form_class=SetForeignKeyInEntitiesActionAdminForm
    )


set_foreign_key.short_description = _("Set foreign keys in selected %(verbose_name_plural)s")
