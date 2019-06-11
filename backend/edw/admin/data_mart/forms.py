#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from salmonella.widgets import SalmonellaMultiIdWidget

from edw.models.term import TermModel
from edw.models.data_mart import DataMartModel
from edw.models.entity import EntityModel
from edw.models.related import DataMartRelationModel

from edw.admin.term.widgets import TermTreeWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField


#==============================================================================
# DataMartAdminForm
#==============================================================================
class DataMartAdminForm(forms.ModelForm):
    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, widget=TermTreeWidget(),
                                           label=_("Terms"))
    ordering = forms.ChoiceField(choices=(), required=True, label=_("Ordering"))
    view_component = forms.ChoiceField(choices=(), required=True, label=_("View component"))

    class Meta:
        model = DataMartModel
        exclude = ()

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        super(DataMartAdminForm, self).__init__(*args, **kwargs)
        if instance is not None:
            entity_model = instance.entities_model
        else:
            entity_model = DataMartModel.get_base_entity_model()
        self.fields['ordering'].choices = entity_model.ORDERING_MODES
        self.fields['view_component'].choices = entity_model.VIEW_COMPONENTS


#==============================================================================
# DataMartRelationInlineForm
#==============================================================================
class DataMartRelationInlineForm(forms.ModelForm):

    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(),
                                       joiner=' / ', label=_('Relation'))

    subjects = forms.ModelMultipleChoiceField(
        queryset=EntityModel.objects.all(),
        label=_('Subjects'),
        widget=SalmonellaMultiIdWidget(DataMartRelationModel._meta.get_field("subjects").rel, admin.site),
        required=False
    )
