#-*- coding: utf-8 -*-
from django.contrib import admin


from edw.models.term import TermModel


class TermAdmin(admin.ModelAdmin):
    pass


admin.site.register(TermModel, TermAdmin)

