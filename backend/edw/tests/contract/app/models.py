# -*- coding: utf-8 -*-
"""
E1: синтетические материализованные модели для характеризационных тестов.

Здесь нет бизнес-логики: только минимальный набор конкретных моделей,
материализующих абстрактные контракты django-edw в приложении
``EDW_APP_LABEL = 'edw_contracts'``:

* ровно один корень ``ContractEntity(BaseEntity)`` и его полиморфные подклассы;
* ``Term`` / ``DataMart`` из штатных defaults;
* relation-модели: EntityRelation, EntityRelatedDataMart,
  AdditionalEntityCharacteristicOrMark, DataMartRelation.

Порядок объявлений важен: deferred-поля разрешаются по мере материализации
абстрактных баз (см. edw/deferred.py), поэтому relation-модели объявлены
до DataMart и Entity.
"""
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import gettext_lazy as _

from edw.models.related import (
    BaseAdditionalEntityCharacteristicOrMark,
    BaseDataMartPermission,
    BaseDataMartRelation,
    BaseEntityRelation,
    BaseEntityRelatedDataMart,
)

# Клиент синтетического контура: нужен DataMartPermission как цель FK customer.
from edw.models.defaults.customer import Customer  # noqa: E402,F401


class AdditionalEntityCharacteristicOrMark(BaseAdditionalEntityCharacteristicOrMark):
    """Материализация связи «сущность — характеристика/метка»."""

    class Meta(BaseAdditionalEntityCharacteristicOrMark.Meta):
        abstract = False


class EntityRelation(BaseEntityRelation):
    """Материализация связи между сущностями."""

    class Meta(BaseEntityRelation.Meta):
        abstract = False


class DataMartRelation(BaseDataMartRelation):
    """Материализация связи витрины данных с термином."""

    class Meta(BaseDataMartRelation.Meta):
        abstract = False


class EntityRelatedDataMart(BaseEntityRelatedDataMart):
    """Материализация связи «сущность — витрина данных»."""

    class Meta(BaseEntityRelatedDataMart.Meta):
        abstract = False


class DataMartPermission(BaseDataMartPermission):
    """Материализация прав доступа клиента к витрине данных."""

    class Meta(BaseDataMartPermission.Meta):
        abstract = False


# Термины и витрины материализуются после relation-моделей.
from edw.models.defaults.term import Term  # noqa: E402,F401

# Штатный edw.models.defaults.data_mart в текущем HEAD ссылается на
# несуществующий BaseDataMart.ENTITIES_VIEW_COMPONENTS, поэтому витрина
# материализуется синтетическим подклассом с тем же контрактом полей.
from edw.models.data_mart import ApiReferenceMixin as DataMartApiReferenceMixin  # noqa: E402
from edw.models.data_mart import BaseDataMart  # noqa: E402


class DataMart(DataMartApiReferenceMixin, BaseDataMart):
    """Материализованная витрина данных синтетического контура."""

    ENTITIES_VIEW_COMPONENTS = (
        (BaseDataMart.ENTITIES_VIEW_COMPONENT_LIST, _('List view')),
    )

    class Meta:
        abstract = False
        verbose_name = _('Data mart')
        verbose_name_plural = _('Data marts')


from edw.models.entity import (  # noqa: E402
    ApiReferenceMixin,
    BaseEntity,
    BaseEntityManager,
    BaseEntityQuerySet,
)


class ContractEntityQuerySet(BaseEntityQuerySet):
    pass


class ContractEntityManager(BaseEntityManager):
    queryset_class = ContractEntityQuerySet


class ContractEntity(ApiReferenceMixin, BaseEntity):
    """Единственный корневой Entity синтетического контура."""

    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True, default='')

    class Meta:
        verbose_name = _('Contract entity')
        verbose_name_plural = _('Contract entities')

    class RESTMeta:
        exclude = ['name']

    objects = ContractEntityManager()

    @property
    def entity_name(self):
        return self.name

    def __str__(self):
        return self.name


class ContractEntityChild(ContractEntity):
    """Полиморфный подкласс корня (отдельная таблица polymorphic child)."""

    code = models.CharField(_('Code'), max_length=32, blank=True, default='')

    class Meta:
        verbose_name = _('Contract entity child')
        verbose_name_plural = _('Contract entity children')

    class RESTMeta:
        exclude = ['name', 'code']

    def __str__(self):
        return '{} [{}]'.format(self.name, self.code)
