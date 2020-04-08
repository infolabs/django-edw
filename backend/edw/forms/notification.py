# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.utils.html import escapejs
from django.utils.safestring import mark_safe
from django.utils.encoding import (
    force_str, force_text, python_2_unicode_compatible,
)
from django.utils.html import conditional_escape, format_html, html_safe
from itertools import chain


class SelectMultiple(forms.SelectMultiple):
    """
    A SelectMultiple with a JavaScript filter interface
    """
    @property
    def media(self):
        # скрипт для скрытия недоступных ролей поля 'notify_to_roles' по полю 'transition'
        js = ["admin/js/core.js", "admin/js/SelectBox.js", "admin/js/SelectFilter2.js", "edw/js/admin/notification.js"]
        return forms.Media(js=[static("%s" % path) for path in js])

    def __init__(self, verbose_name, is_stacked, attrs=None, choices=()):

        self.verbose_name = verbose_name
        self.is_stacked = is_stacked
        super(SelectMultiple, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, choices=()):

        if attrs is None:
            attrs = {}
        attrs['class'] = 'selectfilter'
        if self.is_stacked:
            attrs['class'] += 'stacked'
        output = [super(SelectMultiple, self).render(name, value, attrs, choices)]
        output.append('<script type="text/javascript">addEvent(window, "load", function(e) {')
        output.append('SelectFilter.init("id_%s", "%s", %s); TransitionSelector.init("%s"); });</script>\n'
            % (name, escapejs(self.verbose_name), int(self.is_stacked), name))
        return mark_safe(''.join(output))


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
