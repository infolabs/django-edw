# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

import rest_framework_filters as filters

from edw.models.term import BaseTerm


class TermFilter(filters.FilterSet):
    """
    TermFilter
    """
    active = filters.BooleanFilter(name="active")
    semantic_rule = filters.ChoiceFilter(name="semantic_rule", choices=BaseTerm.SEMANTIC_RULES + (('', _('Any')), ))
    specification_mode = filters.ChoiceFilter(name="specification_mode", choices=BaseTerm.SPECIFICATION_MODES + (('', _('Any')), ))

    class Meta:
        model = BaseTerm
        fields = ['active', 'semantic_rule', 'specification_mode']

