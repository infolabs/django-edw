#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin

from edw.models.related.entity_image import EntityImageModel


#===========================================================================================
# EntityImageInline
#===========================================================================================
class EntityImageInline(SortableInlineAdminMixin, admin.StackedInline):
    model = EntityImageModel
    fk_name = 'entity'
    extra = 1
    ordering = ('order',)

