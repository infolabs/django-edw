#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from edw.models.boundary import BoundaryModel

try:
    from salmonella.admin import SalmonellaMixin
except ImportError:
    from dynamic_raw_id.admin import DynamicRawIDMixin as SalmonellaMixin


# ===========================================================================================
# BoundaryAdmin
# ===========================================================================================
class BoundaryAdmin(SalmonellaMixin, admin.ModelAdmin):
    model = BoundaryModel

    list_display = ['name', 'active']

    fields = ['term', 'order', 'raw_polygons', 'active']

    search_fields = ('term__name', 'raw_polygons')

    salmonella_fields = ('term',)
    dynamic_raw_id_fields = ('term',)


admin.site.register(BoundaryModel, BoundaryAdmin)
