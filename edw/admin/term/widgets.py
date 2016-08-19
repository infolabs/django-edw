#-*- coding: utf-8 -*-
from django import forms
from django.template.loader import render_to_string
from django.conf import settings


class TermTreeWidget(forms.SelectMultiple):
    def __init__(self, attrs=None):
        super(TermTreeWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        return render_to_string(
            'edw/admin/term/widgets/tree.html', {
                'name': name,
                'value': value,
                'attrs': attrs
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
            '/static/edw/lib/jquery/jquery.min.js',
            '/static/edw/js/admin/tree.jquery.js',
        )
