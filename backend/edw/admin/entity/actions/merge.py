# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import objects_action
from edw.tasks import merge_entities
from edw.admin.entity.forms.merge import MergeEntitiesActionAdminForm


def merge(modeladmin, request, queryset):
    """
    ENG: Merge multiple entities

    """
    CHUNK_SIZE = getattr(settings, 'EDW_MERGE_ENTITIES_ACTION_CHUNK_SIZE', 100)

    title = _("Merge multiple entities")

    return objects_action(
        modeladmin, request, queryset, 'merge', merge_entities, title, CHUNK_SIZE,
        admin_form_class=MergeEntitiesActionAdminForm
    )


merge.short_description = _("Merge selected %(verbose_name_plural)s")
