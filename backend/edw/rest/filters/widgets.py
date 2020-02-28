# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import urllib

from django import forms
from django.utils import six
from django_filters.widgets import CSVWidget as OriginCSVWidget


if six.PY3:
    def parse_query(value):
        if isinstance(value, int):
            return [str(value)]
        return urllib.parse.unquote(value).split(',')
else:
    def parse_query(value):
        return urllib.unquote(value).decode('utf8').split(',')


class CSVWidget(OriginCSVWidget):

    def value_from_datadict(self, data, files, name):
        value = super(forms.TextInput, self).value_from_datadict(data, files, name)

        if value is not None:
            try:
                return parse_query(value)
            except AttributeError:
                if isinstance(value, (tuple, list)):
                    return [str(x) for x in value]
                else:
                    return [str(value)]
        return None
