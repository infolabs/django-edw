#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from filer.models import Image
from salmonella.widgets import SalmonellaMultiIdWidget

from edw.models.related import EntityImageModel


#==============================================================================
# EntitiesUpdateImagesAdminForm
#==============================================================================
class EntitiesUpdateImagesAdminForm(forms.Form):

    to_set = forms.ModelMultipleChoiceField(queryset=Image.objects.all(), label=_('Images to set'),
                                              required=False, widget=SalmonellaMultiIdWidget(
            EntityImageModel._meta.get_field("image").rel, admin.site))
    to_set_order = forms.IntegerField(label=_("Order"), required=False)
    to_unset = forms.ModelMultipleChoiceField(queryset=Image.objects.all(), label=_('Images to unset'),
                                              required=False, widget=SalmonellaMultiIdWidget(
            EntityImageModel._meta.get_field("image").rel, admin.site))

    def clean(self):
        cleaned_data = super(EntitiesUpdateImagesAdminForm, self).clean()
        to_set = cleaned_data.get("to_set")
        to_unset = cleaned_data.get("to_unset")

        if not to_set and not to_unset:
            raise forms.ValidationError(
                _("Select images to set or unset")
            )

        return cleaned_data
