#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from salmonella.widgets import SalmonellaMultiIdWidget

from edw.models.data_mart import DataMartModel
from edw.models.related import EntityRelatedDataMartModel


#==============================================================================
# EntitiesUpdateRelatedDataMartsAdminForm
#==============================================================================
class EntitiesUpdateRelatedDataMartsAdminForm(forms.Form):
    to_set_datamarts = forms.ModelMultipleChoiceField(
        queryset=DataMartModel.objects.all(),
        label=_('Data marts to set'),
        required=False,
        widget=SalmonellaMultiIdWidget(
            EntityRelatedDataMartModel._meta.get_field("data_mart").rel,
            admin.site,
        )
    )

    to_unset_datamarts = forms.ModelMultipleChoiceField(
        queryset=DataMartModel.objects.all(),
        label=_('Data marts to unset'),
        required=False,
        widget=SalmonellaMultiIdWidget(
            EntityRelatedDataMartModel._meta.get_field("data_mart").rel,
            admin.site,
        )
    )

    def clean(self):
        cleaned_data = super(EntitiesUpdateRelatedDataMartsAdminForm, self).clean()
        to_set_datamarts = cleaned_data.get("to_set_datamarts")
        to_unset_datamarts = cleaned_data.get("to_unset_datamarts")

        if not (to_set_datamarts or to_unset_datamarts):
            raise forms.ValidationError(
                _("Select related datamarts for set or unset")
            )
