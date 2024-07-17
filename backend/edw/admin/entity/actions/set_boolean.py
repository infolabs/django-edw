# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.base_actions import objects_action
from edw.tasks import set_boolean_in_entities
from edw.admin.entity.forms.set_boolean import SetBooleanInEntitiesActionAdminForm


def set_boolean(modeladmin, request, queryset):
    """
    ENG: Set boolean values in multiple entities

    """
    CHUNK_SIZE = getattr(settings, 'EDW_SET_BOOLEAN_IN_ENTITIES_ACTION_CHUNK_SIZE', 100)

    title = _("Set boolean values in multiple entities")

    return objects_action(
        modeladmin, request, queryset, 'set_boolean', set_boolean_in_entities, title, CHUNK_SIZE,
        admin_form_class=SetBooleanInEntitiesActionAdminForm
    )


set_boolean.short_description = _("Set boolean values in %(verbose_name_plural)s")
