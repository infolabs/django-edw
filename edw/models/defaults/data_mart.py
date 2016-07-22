# -*- coding: utf-8 -*-
from __future__ import unicode_literals
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