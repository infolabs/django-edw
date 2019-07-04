#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from salmonella.widgets import SalmonellaIdWidget

from edw.models.term import TermModel


#==============================================================================
# TermsUpdateParentAdminForm
#==============================================================================
class TermsUpdateParentAdminForm(forms.Form):
    """
    Административная форма обновления термина родителя
    """
    to_set_parent_term_id = forms.ModelChoiceField(
        queryset=TermModel.objects.all(),
        label=_('Term to set'),
        required=True,
        widget=SalmonellaIdWidget(
            TermModel._meta.get_field("parent").rel,
            admin.site,
        )
    )
