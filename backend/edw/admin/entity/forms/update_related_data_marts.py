#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from salmonella.widgets import SalmonellaIdWidget

from edw.models.data_mart import DataMartModel
from edw.models.related import EntityRelatedDataMartModel


#==============================================================================
# EntitiesUpdateRelatedDataMartsAdminForm
#==============================================================================
class EntitiesUpdateRelatedDataMartsAdminForm(forms.Form):

    to_set_datamart = forms.ModelChoiceField(queryset=DataMartModel.objects.all(), label=_('Data mart to set'),
                                              required=False, widget=SalmonellaIdWidget(
            EntityRelatedDataMartModel._meta.get_field("data_mart").rel, admin.site))
    to_unset_datamart = forms.ModelChoiceField(queryset=DataMartModel.objects.all(), label=_('Data mart to unset'),
                                                required=False, widget=SalmonellaIdWidget(
            EntityRelatedDataMartModel._meta.get_field("data_mart").rel, admin.site))

    def clean(self):
        cleaned_data = super(EntitiesUpdateRelatedDataMartsAdminForm, self).clean()
        to_set_datamart = cleaned_data.get("to_set_datamart")
        to_unset_datamart = cleaned_data.get("to_unset_datamart")

        if not (to_set_datamart or to_unset_datamart):
            raise forms.ValidationError(
                _("Select related datamart for set or unset")
            )
