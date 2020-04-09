# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms


class MultiSelectFormField(forms.MultipleChoiceField):
    """
    RUS: Поле формы для MultiSelectField
    с виджетом checkbox
    """
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        super(MultiSelectFormField, self).__init__(*args, **kwargs)


class NotificationForm(forms.ModelForm):
    """
    RUS: Форма для уведомлений
    с динамически формеруемыми choices для ролей пользователей
    """
    notify_to_roles = MultiSelectFormField()

    def __init__(self, *args, **kwargs):

        super(NotificationForm, self).__init__(*args, **kwargs)
        choices = self._meta.model.get_notification_recipients_roles_choices()
        self.fields['notify_to_roles'].choices = choices
        self.fields['transition'].choices = self._meta.model.get_transition_choices()
