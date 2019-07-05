#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from edw.models.term import BaseTerm, TermModel
from edw.admin.term.widgets import TermTreeWidget


#==============================================================================
# EntitiesUpdateTermsAdminForm
#==============================================================================
class EntitiesUpdateTermsAdminForm(forms.Form):
    """
    Форма обновления терминов объектов
    """
    to_set = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, label=_("Terms to set"),
                                            widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False))
    to_unset = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, label=_("Terms to unset"),
                                              widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False))


    def clean(self):
        """
        Словарь проверенных и нормализованных данных формы обновления терминов объектов
        """
        cleaned_data = super(EntitiesUpdateTermsAdminForm, self).clean()
        to_set = cleaned_data.get("to_set")
        to_unset = cleaned_data.get("to_unset")

        if not (to_set or to_unset):
            raise forms.ValidationError(
                _("Select terms for set or unset")
            )
        return cleaned_data