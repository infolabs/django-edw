#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.entity.actions.base_entity_action import base_entity_action
from edw.tasks import make_entities_terms_from_additional_characteristics_or_marks


def make_terms_from_additional_characteristics_or_marks(modeladmin, request, queryset):
    """
    Make terms from additional characteristics or marks
    """
    CHUNK_SIZE = getattr(settings, 'EDW_MAKE_TERMS_FROM_ADDITIONAL_CHARACTERISTICS_OR_MARKS_ACTION_CHUNK_SIZE', 100)

    title = _("Make terms from additional characteristics or marks for multiple entities")

    return base_entity_action(
        modeladmin, request, queryset, 'make_terms_from_additional_characteristics_or_marks',
        make_entities_terms_from_additional_characteristics_or_marks, title, CHUNK_SIZE
    )

make_terms_from_additional_characteristics_or_marks.short_description = _("Make terms from additional characteristics or marks for selected %(verbose_name_plural)s")
