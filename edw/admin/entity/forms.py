#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel, BaseTerm
from edw.models.entity import EntityModel

from django import forms

from edw.admin.term.widgets import TermTreeWidget


#==============================================================================
# EntityAdminForm
#==============================================================================
class EntityAdminForm(forms.ModelForm):
    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all().exclude(system_flags=BaseTerm.system_flags.external_tagging_restriction),
                                          required=False, widget=TermTreeWidget(), label=_("Terms"))

    class Meta:
        model = EntityModel
        exclude = ()