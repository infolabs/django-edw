#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
try:
    from salmonella.widgets import SalmonellaMultiIdWidget
except ImportError:
    from dynamic_raw_id.widgets import DynamicRawIDMultiIdWidget as SalmonellaMultiIdWidget

from edw.admin.customer.widgets import CustomerIdWidget
from edw.admin.mptt.fields import FullPathTreeNodeChoiceField
from edw.admin.term.widgets import TermTreeWidget
from edw.models.customer import CustomerModel
from edw.models.data_mart import DataMartModel
from edw.models.entity import EntityModel
from edw.models.related import DataMartRelationModel
from edw.models.term import TermModel

try:
    subjects_rel = DataMartRelationModel._meta.get_field("subjects").rel
except AttributeError:
    subjects_rel = DataMartRelationModel._meta.get_field("subjects").remote_field

#==============================================================================
# DataMartAdminForm
#==============================================================================
class DataMartAdminForm(forms.ModelForm):
    """
    Определяет данные формы витрины данных
    """
    terms = forms.ModelMultipleChoiceField(queryset=TermModel.objects.all(), required=False, widget=TermTreeWidget(),
                                           label=_("Terms"))
    ordering = forms.ChoiceField(choices=(), required=True, label=_("Ordering"))
    view_component = forms.ChoiceField(choices=(), required=True, label=_("View component"))

    class Meta:
        """
        Определяет дополнительные параметры формы администратора витрины данных
        """
        model = DataMartModel
        exclude = ()

    def __init__(self, *args, **kwargs):
        """
        Конструктор для корректного отображения объектов
        """
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
    """
    Отношения для витрины данных
    """
    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(),
                                       joiner=' / ', label=_('Relation'))

    subjects = forms.ModelMultipleChoiceField(
        queryset=EntityModel.objects.all(),
        label=_('Subjects'),
        widget=SalmonellaMultiIdWidget(subjects_rel, admin.site),
        required=False
    )


#==============================================================================
# DataMartPermissionInlineForm
#==============================================================================
class DataMartPermissionInlineForm(forms.ModelForm):
    """
    Полномочия для витрины данных
    """
    customer = forms.ModelChoiceField(queryset=CustomerModel.objects.all(), widget=CustomerIdWidget(admin.site),
                                      label=_('Customer'))
