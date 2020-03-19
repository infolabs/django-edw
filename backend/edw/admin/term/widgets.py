#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.template.loader import render_to_string


class TermTreeWidget(forms.SelectMultiple):
    """
    Приложение терминов дерева
    """

    def __init__(self, attrs=None, external_tagging_restriction=False, node_template='extended', fix_it=True, active_only=0):
        """
        Конструктор класса
        """
        self.external_tagging_restriction = external_tagging_restriction
        self.node_template = node_template
        self.fix_it = fix_it
        self.active_only = active_only
        super(TermTreeWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None, choices=()):
        """
        Выполняет запрос и возвращает страницу терминов
        """
        if value is None:
            value = []
        return render_to_string(
            'edw/admin/term/widgets/tree/widget.html', {
                'name': name,
                'value': value,
                'attrs': attrs,
                'active_only': self.active_only,
                'node_template': self.node_template,
                'fix_it': self.fix_it,
                'tagging_restriction': self.external_tagging_restriction
            })

    class Media:
        """
        Подключаемые стили CSS и JavaScript
        """
        css = {
            'all': (
                '/static/edw/css/admin/jqtree.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.min.css',
            )
        }
        js = (
            '/static/edw/lib/spin/spin.min.js',
            '/static/edw/js/admin/jquery.compat.js',
            '/static/edw/js/admin/tree.jquery.js'
        )
