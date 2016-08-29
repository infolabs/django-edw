# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
"""
"""
from edw.models.data_mart import BaseDataMart, BaseDataMartManager


class DataMartManager(BaseDataMartManager):
    pass


class DataMart(BaseDataMart):
    """
    Default materialized model for DataMart containing common fields
    """
    objects = DataMartManager()

    class Meta:
        abstract = False
        verbose_name = _("Data mart")
        verbose_name_plural = _("Data marts")