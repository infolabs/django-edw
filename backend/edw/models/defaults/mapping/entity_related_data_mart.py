# -*- coding: utf-8 -*-

from edw.models.related import BaseEntityRelatedDataMart


class EntityRelatedDataMart(BaseEntityRelatedDataMart):
    """
    ENG: Materialize many-to-many relation with data marts.
    RUS: Материализованная связь многие-ко многим с витринами данных.
    """
    class Meta(BaseEntityRelatedDataMart.Meta):
        """
        RUS: Метаданные класса EntityRelation.
        """
        abstract = False
