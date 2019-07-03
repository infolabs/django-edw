#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from edw.models.term import TermModel
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField


# ==============================================================================
# EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm
# ==============================================================================
class EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm(forms.Form):

    to_set_term = FullPathTreeNodeChoiceField(
        queryset=TermModel.objects.attribute_is_characteristic_or_mark(),
        required=False,
        joiner=' / ',
        label=_('Term'),
    )

    value = forms.CharField(
        required=False,
        label=_("Value"),
        max_length=255,
    )

    view_class = forms.CharField(
        required=False,
        label=_('View Class'),
        max_length=255,
        help_text=
        _('Space delimited class attribute, specifies one or more classnames for an entity.'),
    )

    to_unset_term = FullPathTreeNodeChoiceField(
        queryset=TermModel.objects.attribute_is_characteristic_or_mark(),
        required=False,
        joiner=' / ',
        label=_('Term'),
    )

    def clean(self):
        cleaned_data = super(EntitiesUpdateAdditionalCharacteristicsOrMarksAdminForm, self).clean()
        to_set_term = cleaned_data.get("to_set_term")
        to_unset_term = cleaned_data.get("to_unset_term")
        value = cleaned_data.get("value")

        if not (to_set_term or to_unset_term):
            raise forms.ValidationError(
                _("Select term to set or unset")
            )

        if bool(to_set_term) ^ bool(value):
            raise forms.ValidationError(
                _("Set term and value")
            )

        return cleaned_data
