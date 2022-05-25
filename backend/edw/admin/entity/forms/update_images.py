#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from filer.models import Image
try:
    from salmonella.widgets import SalmonellaMultiIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDMultiIdWidget as SalmonellaMultiIdWidget

from edw.models.related.entity_image import EntityImageModel


try:
    image_rel = EntityImageModel._meta.get_field("image").rel
except AttributeError:
    image_rel = EntityImageModel._meta.get_field("image").remote_field

#==============================================================================
# EntitiesUpdateImagesAdminForm
#==============================================================================
class EntitiesUpdateImagesAdminForm(forms.Form):
    """
    Форма обновления изображений объекта
    """
    to_set = forms.ModelMultipleChoiceField(queryset=Image.objects.all(), label=_('Images to set'),
                                              required=False, widget=SalmonellaMultiIdWidget(image_rel, admin.site))
    to_set_order = forms.IntegerField(label=_("Order"), required=False)
    to_unset = forms.ModelMultipleChoiceField(queryset=Image.objects.all(), label=_('Images to unset'),
                                              required=False, widget=SalmonellaMultiIdWidget(image_rel, admin.site))

    def clean(self):
        """
        Словарь проверенных и нормализованных данных формы обновления изображений объекта
        """
        cleaned_data = super(EntitiesUpdateImagesAdminForm, self).clean()
        to_set = cleaned_data.get("to_set")
        to_unset = cleaned_data.get("to_unset")

        if not to_set and not to_unset:
            raise forms.ValidationError(
                _("Select images to set or unset")
            )

        return cleaned_data
