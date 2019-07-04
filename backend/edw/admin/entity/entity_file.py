#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin

from edw.models.related.entity_file import EntityFileModel


#===========================================================================================
# EntityFileInline
#===========================================================================================
class EntityFileInline(SortableInlineAdminMixin, admin.StackedInline):
    """
    Определяет параметры загрузчика файлов
    """
    model = EntityFileModel
    fk_name = 'entity'
    extra = 1
    ordering = ('order',)