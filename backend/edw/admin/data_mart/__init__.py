#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages

from django_mptt_admin.admin import DjangoMpttAdmin
from django_mptt_admin.util import get_tree_from_queryset

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple

from salmonella.admin import SalmonellaMixin

from edw.admin.data_mart.forms import DataMartAdminForm
from edw.admin.mptt.utils import get_mptt_admin_node_template, mptt_admin_node_info_update_with_template


class DataMartAdmin(SalmonellaMixin, DjangoMpttAdmin):
    form = DataMartAdminForm

    save_on_top = True

    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    list_filter = ('active', ) #todo: Add ', ('system_flags', BitFieldListFilter)', Django 1.7 support, fixes https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937

    search_fields = ['name', 'slug']

    salmonella_fields = ('parent', )

    autoescape = False

    class Media:
        css = {
            'all': [
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/datamart.css' if not settings.DEBUG else '/static/edw/assets/less/admin/datamart.css',
                ]
        }

    def delete_model(self, request, obj):
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()

    def get_tree_data(self, qs, max_level):
        def handle_create_node(instance, node_info):
            mptt_admin_node_info_update_with_template(admin_instance=self,
                                                      template=get_mptt_admin_node_template(instance),
                                                      instance=instance,
                                                      node_info=node_info,
                                                      )

        return get_tree_from_queryset(qs, handle_create_node, max_level)

    def i18n_javascript(self, request):
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog

        return javascript_catalog(request, domain='django', packages=['django_mptt_admin', 'edw'])

