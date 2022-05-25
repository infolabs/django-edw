#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
try:
    from salmonella.admin import SalmonellaMixin
except ImportError:
    from dynamic_raw_id.admin import DynamicRawIDMixin as SalmonellaMixin

from edw.models.email_category import EmailCategoryModel


# ===========================================================================================
# EmailCategoryAdmin
# ===========================================================================================
class EmailCategoryAdmin(SalmonellaMixin, admin.ModelAdmin):
    model = EmailCategoryModel

    list_display = ['name', 'active']

    fields = ['term', 'email_masks', 'active']

    search_fields = ('term__name', 'email_masks')

    salmonella_fields = ('term',)
    dynamic_raw_id_fields = ('term',)


admin.site.register(EmailCategoryModel, EmailCategoryAdmin)
