#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

try:
    from salmonella.widgets import SalmonellaMultiIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDMultiIdWidget as SalmonellaMultiIdWidget

from edw.models.data_mart import DataMartModel
from edw.models.related import EntityRelatedDataMartModel

try:
    datamart_rel = EntityRelatedDataMartModel._meta.get_field("data_mart").rel
except AttributeError:
    datamart_rel = EntityRelatedDataMartModel._meta.get_field("data_mart").remote_field

#==============================================================================
# EntitiesUpdateRelatedDataMartsAdminForm
#==============================================================================
class EntitiesUpdateRelatedDataMartsAdminForm(forms.Form):
    """
    Форма обновления связанных витрин данных объекта
    """
    to_set_datamarts = forms.ModelMultipleChoiceField(
        queryset=DataMartModel.objects.all(),
        label=_('Data marts to set'),
        required=False,
        widget=SalmonellaMultiIdWidget(datamart_rel, admin.site)
    )

    to_unset_datamarts = forms.ModelMultipleChoiceField(
        queryset=DataMartModel.objects.all(),
        label=_('Data marts to unset'),
        required=False,
        widget=SalmonellaMultiIdWidget(datamart_rel, admin.site)
    )

    select_across = forms.BooleanField(
        label='',
        required=False,
        initial=0,
        widget=forms.HiddenInput({'class': 'select-across'}),
    )

    def clean(self):
        """
        Словарь проверенных и нормализованных данных формы обновления связанных витрин данных объекта
        """
        cleaned_data = super(EntitiesUpdateRelatedDataMartsAdminForm, self).clean()
        to_set_datamarts = cleaned_data.get("to_set_datamarts")
        to_unset_datamarts = cleaned_data.get("to_unset_datamarts")

        if not (to_set_datamarts or to_unset_datamarts):
            raise forms.ValidationError(
                _("Select related datamarts for set or unset")
            )
