#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


#==============================================================================
# EntitiesUpdateActiveAdminForm
#==============================================================================

BOOLE = (
    ("", ""),
    (True, _("Yes")),
    (False, _("No"))
)

class EntitiesUpdateActiveAdminForm(forms.Form):
    to_set_active = forms.TypedChoiceField(label=_("Active"), choices=BOOLE, initial="",
                                           coerce=lambda x: x == 'True',
                                           widget=forms.Select())
