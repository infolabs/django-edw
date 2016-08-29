#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel, BaseTerm

from django import forms

from edw.admin.term.widgets import TermTreeWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField


#==============================================================================
# EntityAdminForm
#==============================================================================
class EntityAdminForm(forms.ModelForm):

    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all().exclude(
        system_flags=BaseTerm.system_flags.external_tagging_restriction),
        required=False, widget=TermTreeWidget(), label=_("Terms"))


#==============================================================================
# EntityCharacteristicOrMarkInlineForm
#==============================================================================
class EntityCharacteristicOrMarkInlineForm(forms.ModelForm):

    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_characteristic_or_mark(),
                                       joiner=' / ', label=_('Characteristic or mark'))
