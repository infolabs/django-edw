#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from salmonella.admin import SalmonellaMixin

from edw.models.boundary import BoundaryModel


# ===========================================================================================
# BoundaryAdmin
# ===========================================================================================
class BoundaryAdmin(SalmonellaMixin, admin.ModelAdmin):
    model = BoundaryModel

    list_display = ['name', 'active']

    fields = ['term', 'raw_polygons', 'active']

    search_fields = ('term__name', 'raw_polygons')

    salmonella_fields = ('term',)


admin.site.register(BoundaryModel, BoundaryAdmin)