#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from edw.admin.data_mart.forms import (
    DataMartAdminForm,
    DataMartRelationInlineForm,
    DataMartPermissionInlineForm,
)
from edw.models.related import DataMartRelationModel, DataMartPermissionModel
from edw.admin.mptt.tree import EdwMpttAdmin


class DataMartAdmin(EdwMpttAdmin):
    """
    Определяет данные панели администратора витрины данных
    """
    form = DataMartAdminForm

    try:
        from edw.admin.data_mart.actions.update_terms import update_terms
        actions = [update_terms]
    except ModuleNotFoundError:
        pass

    # todo: Add ', ('system_flags', BitFieldListFilter)',
    # Django 1.7 support, fixes
    # https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937
    list_filter = ('active', )

    list_display = ['name', 'parent', 'view_class', 'active']

    fieldsets = (
        ("", {
            'fields': ('parent', 'name', 'slug', 'path', 'view_component', 'ordering', 'limit',
                       'view_class', 'active', 'system_flags', 'terms', 'description'),
        }),
    )

    search_fields = ['name', 'id', 'slug', 'parent__name', 'view_class']

    change_tree_template = 'edw/admin/data_mart/change_list.html'

    class Media:
        """
            Файл стилей CSS (иконочные шрифты, стиль для витрины данных)
        """
        css = {
            'all': [
                '/static/edw/css/admin/datamart.min.css',
                '/static/edw/css/admin/jqtree.css',
                '/static/edw/css/admin/salmonella.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.min.css'
            ],

        }
        js = (
            '/static/edw/lib/spin/spin.min.js',
            '/static/edw/js/admin/jquery.compat.js',
            '/static/edw/js/admin/tree.jquery.js'
        )


#===========================================================================================
# DataMartRelationInline
#===========================================================================================
class DataMartRelationInline(admin.TabularInline):
    model = DataMartRelationModel

    fields = ['term', 'direction', 'subjects']

    salmonella_fields = ('parent', 'subjects')
    dynamic_raw_id_fields = ('parent', 'subjects')

    fk_name = 'data_mart'

    extra = 1

    form = DataMartRelationInlineForm


#===========================================================================================
# DataMartPermissionInline
#===========================================================================================
class DataMartPermissionInline(admin.TabularInline):
    model = DataMartPermissionModel

    fields = ['customer', 'can_add', 'can_change', 'can_delete']

    salmonella_fields = ('customer', )
    dynamic_raw_id_fields = ('customer', )

    fk_name = 'data_mart'

    extra = 1

    form = DataMartPermissionInlineForm
