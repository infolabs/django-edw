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
    EntityImageModel,
)
from filer.models import Image

from edw.admin.term.widgets import TermTreeWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField


#==============================================================================
# EntityAdminForm
#==============================================================================
class EntityAdminForm(forms.ModelForm):

    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all().exclude(
        system_flags=BaseTerm.system_flags.external_tagging_restriction),
        required=False, widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False), label=_("Terms"))


#==============================================================================
# EntityCharacteristicOrMarkInlineForm
#==============================================================================
class EntityCharacteristicOrMarkInlineForm(forms.ModelForm):

    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_characteristic_or_mark(),
                                       joiner=' / ', label=_('Characteristic or mark'))


#==============================================================================
# EntityRelationInlineForm
#==============================================================================
class EntityRelationInlineForm(forms.ModelForm):

    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(),
                                       joiner=' / ', label=_('Relation'))

    to_entity = forms.ModelChoiceField(queryset=EntityModel.objects.all(), label=_('Target'),
                                       widget=SalmonellaIdWidget(
                                           EntityRelationModel._meta.get_field("to_entity").rel, admin.site))


#==============================================================================
# EntityRelatedDataMartInlineForm
#==============================================================================
class EntityRelatedDataMartInlineForm(forms.ModelForm):
    data_mart = forms.ModelChoiceField(queryset=DataMartModel.objects.all(), label=_('Data mart'),
                                       widget=SalmonellaIdWidget(
                                           EntityRelatedDataMartModel._meta.get_field("data_mart").rel, admin.site))


#==============================================================================
# EntitiesUpdateTermsAdminForm
#==============================================================================
class EntitiesUpdateTermsAdminForm(forms.Form):
    to_set = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, label=_("Terms to set"),
                                            widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False))
    to_unset = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, label=_("Terms to unset"),
                                              widget=TermTreeWidget(external_tagging_restriction=True, fix_it=False))


    def clean(self):
        cleaned_data = super(EntitiesUpdateTermsAdminForm, self).clean()
        to_set = cleaned_data.get("to_set")
        to_unset = cleaned_data.get("to_unset")

        if not (to_set or to_unset):
            raise forms.ValidationError(
                _("Select terms for set or unset")
            )
        return cleaned_data


#==============================================================================
# EntitiesUpdateRelationAdminForm
#==============================================================================
class EntitiesUpdateRelationAdminForm(forms.Form):

    to_set_term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(), required=False,
                                       joiner=' / ', label=_('Relation to set'))

    to_set_target = forms.ModelChoiceField(queryset=EntityModel.objects.all(), label=_('Target to set'),
                                              required=False, widget=SalmonellaIdWidget(
            EntityRelationModel._meta.get_field("to_entity").rel, admin.site))

    to_unset_term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(), required=False,
                                              joiner=' / ', label=_('Relation to unset'))

    to_unset_target = forms.ModelChoiceField(queryset=EntityModel.objects.all(), label=_('Target to unset'),
                                                required=False, widget=SalmonellaIdWidget(
            EntityRelationModel._meta.get_field("to_entity").rel, admin.site))

    def clean(self):
        cleaned_data = super(EntitiesUpdateRelationAdminForm, self).clean()
        to_set_term = cleaned_data.get("to_set_term")
        to_set_target = cleaned_data.get("to_set_target")

        to_unset_term = cleaned_data.get("to_unset_term")
        to_unset_target = cleaned_data.get("to_unset_target")

        if not (to_set_term or to_unset_term):
            raise forms.ValidationError(
                _("Select relation for set or unset")
            )

        if bool(to_set_term) ^ bool(to_set_target):
            raise forms.ValidationError(
                _("Select relation and target for set")
            )

        if bool(to_unset_term) ^ bool(to_unset_target):
            raise forms.ValidationError(
                _("Select relation and target for unset")
            )
        return cleaned_data



class EntitiesUpdateImagesAdminForm(forms.Form):

    to_set = forms.ModelChoiceField(queryset=Image.objects.all(), label=_('Image to set'),
                                              required=False, widget=SalmonellaIdWidget(
            EntityImageModel._meta.get_field("image").rel, admin.site))

    to_unset = forms.ModelChoiceField(queryset=Image.objects.all(), label=_('Image to unset'),
                                              required=False, widget=SalmonellaIdWidget(
            EntityImageModel._meta.get_field("image").rel, admin.site))

    def clean(self):
        cleaned_data = super(EntitiesUpdateImagesAdminForm, self).clean()
        to_set = cleaned_data.get("to_set")
        to_unset = cleaned_data.get("to_unset")

        if not to_set and not to_unset:
            raise forms.ValidationError(
                _("Select image for set or unset")
            )

        return cleaned_data
