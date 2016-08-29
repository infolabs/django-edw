# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related import BaseAdditionalEntityCharacteristicOrMark


class AdditionalEntityCharacteristicOrMark(BaseAdditionalEntityCharacteristicOrMark):
    """Materialize many-to-many relation with terms"""
    class Meta(BaseAdditionalEntityCharacteristicOrMark.Meta):
        abstract = False