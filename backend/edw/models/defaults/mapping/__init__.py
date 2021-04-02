# -*- coding: utf-8 -*-

from edw.models.related import (
    BaseAdditionalEntityCharacteristicOrMark,
    BaseEntityRelation,
    BaseDataMartRelation,
    BaseDataMartPermission
)


class AdditionalEntityCharacteristicOrMark(BaseAdditionalEntityCharacteristicOrMark):
    """
    ENG: Materialize many-to-many relation with terms.
    RUS: Материализованная связь многие-ко многим с терминами.
    """
    class Meta(BaseAdditionalEntityCharacteristicOrMark.Meta):
        """
        RUS: Метаданные класса AdditionalEntityCharacteristicOrMark.
        """
        abstract = False


class EntityRelation(BaseEntityRelation):
    """
    ENG: Materialize many-to-many relation with entities.
    RUS: Материализованная связь многие-ко многим с сущностями.
    """
    class Meta(BaseEntityRelation.Meta):
        """
        RUS: Метаданные класса EntityRelation.
        """
        abstract = False


class DataMartRelation(BaseDataMartRelation):
    """
    ENG: Materialize many-to-many data_mart with relations.
    RUS: Материализованная связь многие-ко многим связанных витрин данных.
    """
    class Meta(BaseDataMartRelation.Meta):
        """
        RUS: Метаданные класса DataMartRelation.
        """
        abstract = False


class DataMartPermission(BaseDataMartPermission):
    """
    ENG: Materialize many-to-many data_mart with customer.
    RUS: Материализованная связь многие-ко многим витрина данных - полномочия пользователя.
    """
    class Meta(BaseDataMartPermission.Meta):
        """
        RUS: Метаданные класса DataMartPermission.
        """
        abstract = False
