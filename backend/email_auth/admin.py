# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from email_auth.models import BannedEmailDomain


class BannedEmailDomainAdmin(admin.ModelAdmin):
    model = BannedEmailDomain
    search_fields = ('domain_name',)
    list_display = ('domain_name',)


admin.site.register(BannedEmailDomain, BannedEmailDomainAdmin)
