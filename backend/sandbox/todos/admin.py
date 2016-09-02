# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.db.models import Max
from django.template.context import Context
from django.template.loader import get_template

from edw.admin.customer import CustomerProxy, CustomerAdmin

from edw.models.term import TermModel
from edw.admin.term import TermAdmin

from edw.models.data_mart import DataMartModel
from edw.admin.data_mart import DataMartAdmin

from edw.admin.entity import TermsTreeFilter, EntityCharacteristicOrMarkInline
from edw.admin.entity.forms import EntityAdminForm

from .models import Todo

from adminsortable2.admin import SortableAdminBase

from django.conf import settings

from ckeditor.widgets import CKEditorWidget


class TodoAdminForm(EntityAdminForm):
    """
    TodoAdminForm Mixin
    """
    description = forms.CharField(widget=CKEditorWidget(), label=_('Description'), required=False)


@admin.register(Todo)
class TodoAdmin(SortableAdminBase, admin.ModelAdmin):

    base_model = Todo

    form = TodoAdminForm

    list_display = ('name', 'entity_type', 'marked', 'active',)

    fieldsets = (
        (None, {
            'fields': ('name', 'active', 'marked', 'priority', 'direction', 'terms', 'description'),
        }),
    )

    class Media:
        css = {
            'all': (
                '/static/edw/css/admin/jqtree.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.css' if not settings.DEBUG else '/static/edw/assets/less/admin/term.css',
            )
        }
        js = (
            '/static/edw/lib/spin/spin.min.js',
            '/static/edw/js/admin/tree.jquery.js'
        )

    search_fields = ('name',)

    list_filter = ('active', 'marked', TermsTreeFilter)
    list_per_page = 250
    list_max_show_all = 1000

    inlines = [EntityCharacteristicOrMarkInline]

    def save_model(self, request, obj, form, change):
        if not change:
            # since SortableAdminMixin is missing on this class, ordering has to be computed by hand
            max_order = self.base_model.objects.aggregate(max_order=Max('order'))['max_order']
            obj.order = max_order + 1 if max_order else 1
        super(TodoAdmin, self).save_model(request, obj, form, change)


    def render_text_index(self, instance):
        template = get_template('search/indexes/sample/adultbook_text.txt')
        return template.render(Context({'object': instance}))


    render_text_index.short_description = _("Text Index")


admin.site.register(CustomerProxy, CustomerAdmin)


admin.site.register(TermModel, TermAdmin)


admin.site.register(DataMartModel, DataMartAdmin)

