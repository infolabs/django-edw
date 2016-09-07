#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel, BaseTerm
from edw.models.data_mart import DataMartModel

from edw.admin.term.widgets import TermTreeWidget


#==============================================================================
# DataMartAdminForm
#==============================================================================
class DataMartAdminForm(forms.ModelForm):
    terms = forms.ModelMultipleChoiceField(
        queryset=TermModel.objects.all().exclude(system_flags=BaseTerm.system_flags.external_tagging_restriction),
        required=False, widget=TermTreeWidget(), label=_("Terms"))

    class Meta:
        model = DataMartModel
        exclude = ()