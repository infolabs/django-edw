#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin, messages
from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from django_mptt_admin.admin import DjangoMpttAdmin
from edw.models.term import TermModel


class TermAdmin(DjangoMpttAdmin):
    save_on_top = True

    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    list_filter = ('active', 'semantic_rule', 'specification_mode') #todo: Add ', ('attributes', BitFieldListFilter)', Django 1.7 support, fixes https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937

    search_fields = ['name', 'slug']

    def delete_model(self, request, obj):
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()


admin.site.register(TermModel, TermAdmin)

