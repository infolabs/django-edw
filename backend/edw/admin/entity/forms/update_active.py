#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

#==============================================================================
# EntitiesUpdateActiveAdminForm
#==============================================================================
class EntitiesUpdateActiveAdminForm(forms.Form):
    to_set_active = forms.BooleanField(label=_("Active"), initial=True, required=False)
