#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib.admin.templatetags.admin_static import static
from django.utils.html import escapejs
from django.utils.safestring import mark_safe


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

    def render(self, name, value, attrs=None, renderer=None):
        # render(name, value, attrs=None, renderer=None)
        if attrs is None:
            attrs = {}
        attrs['class'] = 'selectfilter'
        if self.is_stacked:
            attrs['class'] += 'stacked'
        context = self.get_context(name, value, attrs)
        output = [self._render(self.template_name, context, renderer)]
        output.append('<script type="text/javascript">addEvent(window, "load", function(e) {')
        output.append('TransitionSelector.init("%s"); });</script>\n'% name)
        return mark_safe(''.join(output))


