#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel
from edw.models.data_mart import DataMartModel

from edw.admin.term.widgets import TermTreeWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField


#==============================================================================
# DataMartAdminForm
#==============================================================================
class DataMartAdminForm(forms.ModelForm):
    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, widget=TermTreeWidget(),
                                           label=_("Terms"))

    ordering = forms.ChoiceField(choices=(), required=True, label=_("Ordering"))

    class Meta:
        model = DataMartModel
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(DataMartAdminForm, self).__init__(*args, **kwargs)
        self.fields['ordering'].choices = self.Meta.model.ENTITIES_ORDERING_MODES


#==============================================================================
# DataMartRelationInlineForm
#==============================================================================
class DataMartRelationInlineForm(forms.ModelForm):

    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(),
                                       joiner=' / ', label=_('Relation'))