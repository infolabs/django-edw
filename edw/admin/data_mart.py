#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
#from django.contrib import admin
from django_mptt_admin.admin import DjangoMpttAdmin

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple

#from edw.models.data_mart import DataMartModel


class DataMartAdmin(DjangoMpttAdmin):
    save_on_top = True

    prepopulated_fields = {"slug": ("name",)}

    formfield_overrides = {
        BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }

    list_filter = ('active', ) #todo: Add ', ('system_flags', BitFieldListFilter)', Django 1.7 support, fixes https://github.com/coagulant/django-bitfield/commit/fbbececd6e60c9a804846050da8bf258bd7f2937

    search_fields = ['name', 'slug']

    def delete_model(self, request, obj):
        if obj.system_flags.delete_restriction:
            storage = messages.get_messages(request)
            storage.used = True
            messages.error(request, obj.system_flags.get_label('delete_restriction'))
        else:
            obj.delete()


#admin.site.register(DataMartModel, DataMartAdmin)

