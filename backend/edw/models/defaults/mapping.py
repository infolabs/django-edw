# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from edw.models.related import (
    BaseAdditionalEntityCharacteristicOrMark,
    BaseEntityRelation,
    # BaseEntityRelatedDataMart,
    BaseEntityImage
)


class AdditionalEntityCharacteristicOrMark(BaseAdditionalEntityCharacteristicOrMark):
    """Materialize many-to-many relation with terms"""
    class Meta(BaseAdditionalEntityCharacteristicOrMark.Meta):
        abstract = False


class EntityRelation(BaseEntityRelation):
    """Materialize many-to-many relation with entities"""
    class Meta(BaseEntityRelation.Meta):
        abstract = False


# class EntityRelatedDataMart(BaseEntityRelatedDataMart):
#     """Materialize many-to-many relation with data marts"""
#     class Meta(BaseEntityRelatedDataMart.Meta):
#         abstract = False


class EntityImage(BaseEntityImage):
    """Materialize many-to-many relation with images"""
    class Meta(BaseEntityImage.Meta):
        abstract = False