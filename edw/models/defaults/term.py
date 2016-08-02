# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
"""
"""
from edw.models.term import BaseTerm, BaseTermManager


class TermManager(BaseTermManager):
    pass


class Term(BaseTerm):
    """
    Default materialized model for BaseTerm containing common fields
    """
    objects = TermManager()

    class Meta:
        abstract = False
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")