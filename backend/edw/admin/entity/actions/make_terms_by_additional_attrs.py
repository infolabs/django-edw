#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from edw.admin.entity.actions.base_entity_action import base_entity_action
from edw.tasks import entities_make_terms_by_additional_attrs


def make_terms_by_additional_attrs(modeladmin, request, queryset):
    """
    ENG: Make terms by additional attributes
    RUS: Создает термины по дополнительным атрибутам
    """
    CHUNK_SIZE = getattr(settings, 'EDW_MAKE_TERMS_BY_ADDITIONAL_ATTRS_ACTION_CHUNK_SIZE', 100)

    title = _("Make terms by additional attributes")

    return base_entity_action(
        modeladmin, request, queryset, 'make_terms_by_additional_attrs',
        entities_make_terms_by_additional_attrs, title, CHUNK_SIZE
    )

make_terms_by_additional_attrs.short_description = _("Make terms by additional attributes for selected %(verbose_name_plural)s")
