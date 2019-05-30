#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.entity.actions.base_entity_action import base_entity_action
from edw.tasks import remove_entities_additional_characteristics_or_marks_with_exists_value_term


def remove_additional_characteristics_or_marks_with_exists_value_term(modeladmin, request, queryset):
    """
    Remove additional characteristics or marks with exists value term
    """
    CHUNK_SIZE = getattr(settings, 'EDW_REMOVE_ADDITIONAL_CHARACTERISTICS_OR_MARKS_WITH_EXISTS_VALUE_TERM_ACTION_CHUNK_SIZE', 100)

    title = _("Remove additional characteristics or marks with exists value term")

    return base_entity_action(
        modeladmin, request, queryset, 'remove_additional_characteristics_or_marks_with_exists_value_term',
        remove_entities_additional_characteristics_or_marks_with_exists_value_term, title, CHUNK_SIZE
    )

remove_additional_characteristics_or_marks_with_exists_value_term.short_description = _("Remove additional characteristics or marks with exists value term for selected %(verbose_name_plural)s")
