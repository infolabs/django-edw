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

from edw.admin.entity import (
    TermsTreeFilter,
    EntityCharacteristicOrMarkInline,
    EntityRelationInline,
    EntityImageInline
)
from edw.admin.entity.forms import EntityAdminForm

from .models import Book, ChildBook, AdultBook

from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin, PolymorphicChildModelFilter
from adminsortable2.admin import SortableAdminMixin

from django.conf import settings

from ckeditor.widgets import CKEditorWidget


class BookAdminForm(EntityAdminForm):
    """
    BookAdminForm Mixin
    """
    description = forms.CharField(widget=CKEditorWidget(), label=_('Description'), required=False)


class ChildBookAdmin(SortableAdminMixin, PolymorphicChildModelAdmin):

    base_model = Book

    form = BookAdminForm

    fieldsets = (
        (None, {
            'fields': ('name', 'created_at', 'slug', 'active', 'age', 'terms', 'description'),
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

    prepopulated_fields = {'slug': ('name',)}

    inlines = [EntityCharacteristicOrMarkInline, EntityRelationInline, EntityImageInline]

    def save_model(self, request, obj, form, change):
        if not change:
            # since SortableAdminMixin is missing on this class, ordering has to be computed by hand
            max_order = self.base_model.objects.aggregate(max_order=Max('order'))['max_order']
            obj.order = max_order + 1 if max_order else 1
        super(ChildBookAdmin, self).save_model(request, obj, form, change)

    def render_text_index(self, instance):
        template = get_template('search/indexes/sample/childbook_text.txt')
        return template.render(Context({'object': instance}))

    render_text_index.short_description = _("Text Index")


class AdultBookAdmin(SortableAdminMixin, PolymorphicChildModelAdmin):

    base_model = Book

    form = BookAdminForm

    fieldsets = (
        (None, {
            'fields': ('name', 'created_at', 'slug', 'active', 'genre', 'terms', 'description'),
        }),
    )

    prepopulated_fields = {'slug': ('name',)}

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

    inlines = [EntityCharacteristicOrMarkInline, EntityRelationInline, EntityImageInline]

    def save_model(self, request, obj, form, change):
        if not change:
            # since SortableAdminMixin is missing on this class, ordering has to be computed by hand
            max_order = self.base_model.objects.aggregate(max_order=Max('order'))['max_order']
            obj.order = max_order + 1 if max_order else 1
        super(AdultBookAdmin, self).save_model(request, obj, form, change)

    def render_text_index(self, instance):
        template = get_template('search/indexes/sample/adultbook_text.txt')
        return template.render(Context({'object': instance}))

    render_text_index.short_description = _("Text Index")


@admin.register(Book)
class BookAdmin(SortableAdminMixin, PolymorphicParentModelAdmin):

    base_model = Book

    form = BookAdminForm

    child_models = ((ChildBook, ChildBookAdmin), (AdultBook, AdultBookAdmin),)

    list_display = ('name', 'slug', 'entity_type', 'active',)

    fieldsets = (
        (None, {
            'fields': ('name', 'created_at', 'slug', 'active', 'description'),
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

    prepopulated_fields = {'slug': ('name',)}

    search_fields = ('name',)

    list_filter = (PolymorphicChildModelFilter, 'active', TermsTreeFilter)
    list_per_page = 250
    list_max_show_all = 1000

    inlines = [EntityCharacteristicOrMarkInline, EntityRelationInline, EntityImageInline]


admin.site.register(CustomerProxy, CustomerAdmin)


admin.site.register(TermModel, TermAdmin)


admin.site.register(DataMartModel, DataMartAdmin)

