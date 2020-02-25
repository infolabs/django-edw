#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django.conf import settings
from django.contrib import (
    messages,
    admin
)
from django.utils import six

from django_mptt_admin.admin import DjangoMpttAdmin
from django_mptt_admin.util import get_tree_from_queryset
from salmonella.admin import SalmonellaMixin

from edw.admin.data_mart.forms import (
    DataMartAdminForm,
    DataMartRelationInlineForm,
    DataMartPermissionInlineForm,
)
from edw.admin.mptt.utils import get_mptt_admin_node_template, mptt_admin_node_info_update_with_template
from edw.models.related import DataMartRelationModel, DataMartPermissionModel


class DataMartAdmin(SalmonellaMixin, DjangoMpttAdmin):
    """
    Определяет данные панели администратора витрины данных
    """
    form = DataMartAdminForm

    save_on_top = True

    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    list_filter = ('active', ) #todo: Add ', ('system_flags', BitFieldListFilter)', Django 1.7 support, fixes https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937

    list_display = ['name', 'parent', 'view_class', 'active']

    fieldsets = (
        ("", {
            'fields': ('parent', 'name', 'slug', 'path', 'view_component', 'ordering', 'limit',
                       'view_class', 'active', 'system_flags', 'terms', 'description'),
        }),
    )

    readonly_fields = ['path']

    search_fields = ['name', 'id', 'slug', 'parent__name', 'view_class']

    salmonella_fields = ('parent',)

    change_tree_template = 'edw/admin/data_mart/change_list.html'

    autoescape = False

    class Media:
        """
            Файл стилей CSS (иконочные шрифты, стиль для витрины данных)
        """
        css = {
            'all': [
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/datamart.min.css',
            ]
        }

    def delete_model(self, request, obj):
        """
        Удаляет объект, содержащий системные флаги, у которых нет ограничения на удаление
        """
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()

    def get_tree_data(self, qs, max_level, filters_params=None):
        """
        Возвращает данные дерева панели администратора MPTT в виде html-шаблона, 
        соответсвующие условиям запроса, отображающий максимальный уровень 
        """

        def handle_create_node(instance, node_info):
            """
            Обновляет панель администрирования MPTT в виде шаблона html
            """
            if six.PY3:
                node_info['label'] = node_info['name']
            mptt_admin_node_info_update_with_template(admin_instance=self,
                                                      template=get_mptt_admin_node_template(instance),
                                                      instance=instance,
                                                      node_info=node_info,
                                                      )
        if six.PY3:
            ret = get_tree_from_queryset(qs, handle_create_node, max_level, 'name')
        else:
            ret = get_tree_from_queryset(qs, handle_create_node, max_level)
        return ret

    def i18n_javascript(self, request):
        """
        Возвращает каталог библиотеки Javascript для перевода текста
        """
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog

        return javascript_catalog(request, domain='django', packages=['django_mptt_admin', 'edw'])


#===========================================================================================
# DataMartRelationInline
#===========================================================================================
class DataMartRelationInline(admin.TabularInline):
    model = DataMartRelationModel

    fields=['term', 'direction', 'subjects']

    salmonella_fields = ('parent', 'subjects')

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

    fk_name = 'data_mart'

    extra = 1

    form = DataMartPermissionInlineForm

