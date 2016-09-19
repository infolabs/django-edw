#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.conf import settings
from django.template.loader import render_to_string


class TermTreeWidget(forms.SelectMultiple):

    def __init__(self, attrs=None, external_tagging_restriction=False, node_template='extended', fix_it=True):
        self.external_tagging_restriction = external_tagging_restriction
        self.node_template = node_template
        self.fix_it = fix_it
        super(TermTreeWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        return render_to_string(
            'edw/admin/term/widgets/tree/widget.html', {
                'name': name,
                'value': value,
                'attrs': attrs,
                'active_only': 0,
                'node_template': self.node_template,
                'fix_it': self.fix_it,
                'tagging_restriction': self.external_tagging_restriction
            })

    class Media:
        css = {
            'all': (
                '/static/edw/css/admin/jqtree.css',
                '/static/edw/lib/font-awesome/css/font-awesome.min.css',
                '/static/edw/css/admin/term.css' if not settings.DEBUG else '/static/edw/assets/less/admin/term.css',
            )
        }
        js = (
            '/static/edw/lib/spin/spin.min.js',
            '/static/edw/js/admin/tree.jquery.js'
        )
