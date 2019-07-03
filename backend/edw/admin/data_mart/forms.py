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
    """
    Определяет данные формы администратора витрины данных
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
    Определяет значение поля термина формы для узлов дерева
    """
    term = FullPathTreeNodeChoiceField(queryset=TermModel.objects.attribute_is_relation(),
                                       joiner=' / ', label=_('Relation'))