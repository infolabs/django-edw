#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from salmonella.widgets import SalmonellaIdWidget

from edw.models.term import BaseTerm, TermModel
from edw.models.entity import EntityModel
from edw.models.data_mart import DataMartModel
from edw.models.related import (
    EntityRelationModel,
    EntityRelatedDataMartModel,
)
from edw.models.mixins.entity.customer_category import CustomerCategoryMixin

from edw.admin.term.widgets import TermTreeWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField

from update_terms import EntitiesUpdateTermsAdminForm
from update_relations import EntitiesUpdateRelationAdminForm
from update_additional_characteristics_or_marks import EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm
from update_related_data_marts import EntitiesUpdateRelatedDataMartsAdminForm
from update_states import EntitiesUpdateStateAdminForm
from update_active import EntitiesUpdateActiveAdminForm
from base_entity_action import BaseEntityActionAdminForm


#==============================================================================
# EntityAdminForm
#==============================================================================
class EntityAdminForm(forms.ModelForm):
    """
    Форма администратора объекта
    """
    # messages = {
    #     'has_view_layout_error': _("The view layout of the publication isn't defined"),
    # }

    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all().exclude(
        system_flags=BaseTerm.system_flags.external_tagging_restriction),
        required=False, widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False, active_only=1), label=_("Terms"))

    def clean_terms(self):
        data = self.cleaned_data['terms']

        if isinstance(self.instance, CustomerCategoryMixin):
            print ("!!!!!!!!!!!!!!!!!!")
            print ("!!!!!!!!!!!!!!!!!!")
            print ("!!!!! CustomerCategoryMixin !!!!!")
            print ("!!!!!!!!!!!!!!!!!!")
            print ("!!!!!!!!!!!!!!!!!!")

            ids_set = self.instance.all_customer_categories_terms_ids_set


            new_data = []
            for x in data:
                if x.id not in ids_set:
                    new_data.append(x)
                else:
                    print ("**** remove ***", x)

            data = new_data

        print ("#### TODO HERE ####")

        print (">>>>> CLEAN_TERMS <<<<<", data)


        self.instance._clean_terms = data

        return data

    def clean(self):
        """
        RUS: Словарь проверенных и нормализованных данных формы.
        Вызывает ошибку валидации формы, если нет требуемых терминов.
        """
        cleaned_data = super(EntityAdminForm, self).clean()

        print ("++++ Cleaned data ++++", cleaned_data)

        # view layout
        # if not (set([v.id for (k, v) in get_views_layouts().items()]) & set([x.id for x in cleaned_data.get("terms")])):
        #     raise forms.ValidationError(self.messages['has_view_layout_error'])

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
                                       widget=SalmonellaIdWidget(
                                           EntityRelationModel._meta.get_field("to_entity").rel, admin.site))


#==============================================================================
# EntityRelatedDataMartInlineForm
#==============================================================================
class EntityRelatedDataMartInlineForm(forms.ModelForm):
    """
    Форма связанной витрины данных
    """
    data_mart = forms.ModelChoiceField(queryset=DataMartModel.objects.all(), label=_('Data mart'),
                                       widget=SalmonellaIdWidget(
                                           EntityRelatedDataMartModel._meta.get_field("data_mart").rel, admin.site))


