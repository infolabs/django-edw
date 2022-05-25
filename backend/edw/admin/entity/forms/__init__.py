#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

try:
    from salmonella.widgets import SalmonellaIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDWidget as SalmonellaIdWidget

from edw.models.term import BaseTerm, TermModel
from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.models.related import (
    EntityRelationModel,
    EntityRelatedDataMartModel,
)

from edw.admin.term.widgets import TermTreeWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField

from .update_terms import EntitiesUpdateTermsAdminForm
from .update_relations import EntitiesUpdateRelationAdminForm
from .update_additional_characteristics_or_marks import EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm
from .update_related_data_marts import EntitiesUpdateRelatedDataMartsAdminForm
from .update_states import EntitiesUpdateStateAdminForm
from .update_active import EntitiesUpdateActiveAdminForm


try:
    to_entity_rel = EntityRelationModel._meta.get_field("to_entity").rel
except AttributeError:
    to_entity_rel = EntityRelationModel._meta.get_field("to_entity").remote_field

try:
    datamart_rel = EntityRelatedDataMartModel._meta.get_field("data_mart").rel
except AttributeError:
    datamart_rel = EntityRelatedDataMartModel._meta.get_field("data_mart").remote_field

#==============================================================================
# EntityAdminForm
#==============================================================================
class EntityAdminForm(forms.ModelForm):
    """
    Форма администратора объекта
    """

    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all().exclude(
        system_flags=BaseTerm.system_flags.external_tagging_restriction),
        required=False, widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False, active_only=1), label=_("Terms"))

    def clean_terms(self):
        return self.instance.clean_terms(self.cleaned_data['terms'])


#==============================================================================
# EntityCharacteristicOrMarkInlineForm
#==============================================================================
class EntityCharacteristicOrMarkInlineForm(forms.ModelForm):
    """
    Форма характеристик или меток объекта
    """
    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_characteristic_or_mark(),
                                       joiner=' / ', label=_('Characteristic or mark'))


#==============================================================================
# EntityRelationInlineForm
#==============================================================================
class EntityRelationInlineForm(forms.ModelForm):
    """
    Форма отношений объекта 
    """
    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(),
                                       joiner=' / ', label=_('Relation'))

    to_entity = forms.ModelChoiceField(queryset=EntityModel.objects.all(), label=_('Target'),
                                       widget=SalmonellaIdWidget(to_entity_rel, admin.site))


#==============================================================================
# EntityRelatedDataMartInlineForm
#==============================================================================
class EntityRelatedDataMartInlineForm(forms.ModelForm):
    """
    Форма связанной витрины данных
    """
    data_mart = forms.ModelChoiceField(queryset=DataMartModel.objects.all(), label=_('Data mart'),
                                       widget=SalmonellaIdWidget(datamart_rel, admin.site))
