#-*- coding: utf-8 -*-
from __future__ import unicode_literals
import six

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple

from salmonella.admin import SalmonellaMixin

from django_mptt_admin.admin import DjangoMpttAdmin
from django_mptt_admin.util import get_tree_from_queryset

from django.forms import Media
from django.contrib import messages
from django.conf import settings

from edw.admin.mptt.utils import get_mptt_admin_node_template, mptt_admin_node_info_update_with_template


class EdwMpttAdmin(SalmonellaMixin, DjangoMpttAdmin):

    readonly_fields = ['path']

    salmonella_fields = ('parent',)

    autoescape = False

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    save_on_top = True

    prepopulated_fields = {"slug": ("name",)}

    def get_list_filter(self, request):
        return super(EdwMpttAdmin, self).get_list_filter(request) if request.path.endswith('/grid/') else ()

    def delete_model(self, request, obj):
        """
        Удаляет объект, если не существует ограничения к удалению
        """
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()

    def get_tree_media(self):
        js = [
            '/static/django_mptt_admin/jquery_namespace.js',
            '/static/django_mptt_admin/django_mptt_admin.js',
        ]
        css = {
            'all': [
                '/static/edw/css/admin/django_mptt_admin.css',
            ]
        }
        tree_media = Media(js=js, css=css)
        return self.media + tree_media

    def get_tree_data(self, qs, max_level, filters_params=None):
        """
        Создает дерево витрины данных
        """
        def handle_create_node(instance, node_info):
            """
            Вспомогательная функция создания дерева витрины данных.
            Возвращает обновленную html-страницу дерева
            """
            if six.PY3:
                node_info['label'] = node_info['name']

            mptt_admin_node_info_update_with_template(admin_instance=self,
                                                      template=get_mptt_admin_node_template(instance),
                                                      instance=instance,
                                                      node_info=node_info)
        args = [qs, handle_create_node, max_level]
        if six.PY3:
            args.append('name')
        return get_tree_from_queryset(*args)

    def i18n_javascript(self, request):
        """
        Библиотека переводов текста
        """
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog

        return javascript_catalog(request, domain='django', packages=['django_mptt_admin', 'edw'])
