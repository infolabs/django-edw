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
    ENG: Default materialized model for BaseTerm containing common fields.
    RUS: Материализованная по умолчанию модель для BaseTerm, содержащая общие поля.
    """
    objects = TermManager()

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = False
        verbose_name = _("Term")
        verbose_name_plural = _("Topic model")