#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.contrib import admin

from adminsortable2.admin import SortableInlineAdminMixin

from edw.models.related.data_mart_image import DataMartImageModel


# ===========================================================================================
# EntityImageInline
# ===========================================================================================
class DataMartImageInline(SortableInlineAdminMixin, admin.StackedInline):
    """
     Определяет параметры изображения для витрины данных
    """
    model = DataMartImageModel
    fk_name = 'data_mart'
    extra = 1
    ordering = ('order',)