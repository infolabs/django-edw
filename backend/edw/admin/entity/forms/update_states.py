#-*- coding: utf-8 -*-
from __future__ import unicode_literals


from django import forms
from django.utils.translation import ugettext_lazy as _

from edw.models.data_mart import DataMartModel


#==============================================================================
# EntitiesUpdateStateAdminForm
#==============================================================================
class EntitiesUpdateStateAdminForm(forms.Form):
    """
    Форма обновления состояния (статуса) объектов
    """
    state = forms.ChoiceField(choices=(('', _("-"*9)),), label=_('State'))

    def __init__(self, *args, **kwargs):
        """
        Конструктор для корректного отображения объектов
        """
        entities_model = kwargs.pop('entities_model', None)
        super(EntitiesUpdateStateAdminForm, self).__init__(*args, **kwargs)
        if entities_model is None:
            entities_model = DataMartModel.get_base_entity_model()
        transition_states = getattr(entities_model, 'TRANSITION_TARGETS', {})
        if transition_states:
            choices = []
            for k, v in list(transition_states.items()):
                choices.append((k, v))
            self.fields['state'].choices = choices

    def clean(self):
        """
        Словарь проверенных и нормализованных данных формы обновления состояния (статуса) объектов
        """
        cleaned_data = super(EntitiesUpdateStateAdminForm, self).clean()
        state = cleaned_data.get("state")

        if not state:
            raise forms.ValidationError(
                _("Selected entities is not FSM instances")
            )

        return cleaned_data
