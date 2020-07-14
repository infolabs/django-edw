# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _


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
    notify_to_roles = MultiSelectFormField(label=_('Notify to roles'), help_text=_('You can set multiple flags at the same time. The target audience of the region includes only intersections in the regional terms of persons. Target audience - includes intersections in any common terms (Region, themes, social networks...)'))

    def __init__(self, *args, **kwargs):

        super(NotificationForm, self).__init__(*args, **kwargs)
        choices = self._meta.model.get_notification_recipients_roles_choices()
        self.fields['notify_to_roles'].choices = choices
        self.fields['transition'].choices = self._meta.model.get_transition_choices()
