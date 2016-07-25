# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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