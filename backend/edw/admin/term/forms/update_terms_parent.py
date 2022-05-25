#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

try:
    from salmonella.widgets import SalmonellaIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDWidget as SalmonellaIdWidget

from edw.models.term import TermModel

try:
    rel = TermModel._meta.get_field("parent").rel
except AttributeError:
    rel = TermModel._meta.get_field("parent").remote_field


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
        widget=SalmonellaIdWidget(rel, admin.site)
    )
