# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from edw.tasks import update_entities_terms
from edw.admin.base_actions import update_terms as base_update_terms


def update_terms(modeladmin, request, queryset):
    return base_update_terms.update_terms(modeladmin, request, queryset, update_entities_terms)


update_terms.short_description = _("Modify terms for selected %(verbose_name_plural)s")
