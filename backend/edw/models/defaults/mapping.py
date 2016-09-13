# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related import (
    BaseAdditionalEntityCharacteristicOrMark,
    BaseEntityRelation
)


class AdditionalEntityCharacteristicOrMark(BaseAdditionalEntityCharacteristicOrMark):
    """Materialize many-to-many relation with terms"""
    class Meta(BaseAdditionalEntityCharacteristicOrMark.Meta):
        abstract = False


class EntityRelation(BaseEntityRelation):
    """Materialize many-to-many relation with entities"""
    class Meta(BaseEntityRelation.Meta):
        abstract = False
