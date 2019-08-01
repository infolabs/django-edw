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
    ENG: Default materialized model for DataMart containing common fields.
    RUS: Материализованная по умолчанию модель Витрины данных, содержащая общие поля.
    """
    ENTITIES_TILE_VIEW_COMPONENT = 'tile'

    ENTITIES_VIEW_COMPONENTS = (
        (ENTITIES_TILE_VIEW_COMPONENT, _('Tile view')),
    ) + BaseDataMart.ENTITIES_VIEW_COMPONENTS

    objects = DataMartManager()

    class Meta:
        """
        RUS: Метаданные класса.
        """
        abstract = False
        verbose_name = _("Data mart")
        verbose_name_plural = _("Data marts")
