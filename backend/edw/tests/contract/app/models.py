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


# ---------------------------------------------------------------------------
# E11/R4: synthetic effect-set probes (test-only, deliberately no business
# logic).  The managers can be made to fail *measurement* from a test, so the
# product has to prove that an unmeasurable effect set is refused instead of
# being treated as an empty one.  Flags default to off: ordinary tests see a
# normal, fast-deletable related model.
# ---------------------------------------------------------------------------
class SafetyProbeFlags(object):
    """Test-controlled failure injection for the DELETE effect-set probes."""

    refuse_count = False
    refuse_fetch = False


class SafetyProbeQuerySet(models.QuerySet):
    def count(self):
        if SafetyProbeFlags.refuse_count:
            raise RuntimeError('safety probe: count refused')
        return super(SafetyProbeQuerySet, self).count()

    def exists(self):
        if SafetyProbeFlags.refuse_fetch:
            raise RuntimeError('safety probe: existence check refused')
        return super(SafetyProbeQuerySet, self).exists()

    def _fetch_all(self):
        if SafetyProbeFlags.refuse_fetch:
            raise RuntimeError('safety probe: effect rows could not be read')
        return super(SafetyProbeQuerySet, self)._fetch_all()


class FastDeleteProbe(models.Model):
    """A related CASCADE row whose measurement can be made to fail."""

    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name='safety_fast_delete_probes',
    )
    note = models.CharField(max_length=64, blank=True, default='')

    objects = SafetyProbeQuerySet.as_manager()

    class Meta:
        app_label = 'edw_contracts'
        base_manager_name = 'objects'

    def __str__(self):
        return 'FastDeleteProbe(pk={}, term={})'.format(self.pk, self.term_id)


class UnknownEffectProbe(models.Model):
    """A second related row used for the fail-closed measurement control."""

    term = models.ForeignKey(
        Term, on_delete=models.CASCADE, related_name='safety_unknown_effect_probes',
    )
    note = models.CharField(max_length=64, blank=True, default='')

    objects = SafetyProbeQuerySet.as_manager()

    class Meta:
        app_label = 'edw_contracts'
        base_manager_name = 'objects'

    def __str__(self):
        return 'UnknownEffectProbe(pk={}, term={})'.format(self.pk, self.term_id)


class ProtectedProbe(models.Model):
    """A related row with ``on_delete=PROTECT`` (DELETE must fail closed)."""

    term = models.ForeignKey(
        Term, on_delete=models.PROTECT, related_name='safety_protected_probes',
    )
    note = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        app_label = 'edw_contracts'

    def __str__(self):
        return 'ProtectedProbe(pk={}, term={})'.format(self.pk, self.term_id)
