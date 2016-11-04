# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
"""
"""
from edw.models.data_mart import BaseDataMart, BaseDataMartManager, ApiReferenceMixin


class DataMartManager(BaseDataMartManager):
    pass


class DataMart(ApiReferenceMixin, BaseDataMart):
    """
    Default materialized model for DataMart containing common fields
    """
    ENTITIES_ORDER_BY_NAME_ASC = 'name'
    # ENTITIES_ORDER_BY_NAME_DESC = '-name'

    ENTITIES_ORDERING_MODES = (
        (ENTITIES_ORDER_BY_NAME_ASC, _('Alphabetical')),
        # (ENTITIES_ORDER_BY_NAME_DESC, _('Alphabetical: descending')),
    ) + BaseDataMart.ENTITIES_ORDERING_MODES

    objects = DataMartManager()

    class Meta:
        abstract = False
        verbose_name = _("Data mart")
        verbose_name_plural = _("Data marts")