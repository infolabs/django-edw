# -*- coding: utf-8 -*-
"""
E1: контракт материализации моделей EDW (edw/deferred.py).

Фиксируем: ровно один корневой Entity материализуется из BaseEntity, его
полиморфные подклассы допустимы, повторная материализация того же абстрактного
корня отвергается (guard в edw/deferred.py).
"""
from __future__ import unicode_literals

import os
import subprocess
import sys
from pathlib import Path

import pytest

from edw.deferred import ForeignKeyBuilder
from edw.models.data_mart import DataMartModel
from edw.models.entity import BaseEntity, EntityModel
from edw.models.related import (
    AdditionalEntityCharacteristicOrMarkModel,
    EntityRelationModel,
    EntityRelatedDataMartModel,
)
from edw.models.term import TermModel
from edw.tests.contract.app.models import (
    ContractEntity,
    ContractEntityChild,
    DataMart,
)

pytestmark = pytest.mark.django_db

BACKEND_DIR = Path(__file__).resolve().parents[3]


def test_single_root_entity_materialized():
    assert BaseEntity._meta.abstract is True
    assert ContractEntity._meta.abstract is False
    assert EntityModel.materialized is ContractEntity
    assert BaseEntity._materialized_model is ContractEntity
    # ровно одна запись в карте материализации для корня
    entity_roots = [name for abstract, name in ForeignKeyBuilder._materialized_models.items()
                    if abstract == 'BaseEntity']
    assert entity_roots == ['ContractEntity']


def test_polymorphic_child_extends_root_entity():
    assert issubclass(ContractEntityChild, ContractEntity)
    assert ContractEntityChild._meta.abstract is False
    assert ContractEntityChild._meta.proxy is False
    assert ContractEntityChild is not ContractEntity
    # подкласс не переопределяет корень материализации
    assert EntityModel.materialized is ContractEntity


def test_library_relations_materialized_into_synthetic_app():
    materialized_models = (
        EntityModel.materialized,
        TermModel.materialized,
        DataMartModel.materialized,
        EntityRelationModel.materialized,
        AdditionalEntityCharacteristicOrMarkModel.materialized,
        EntityRelatedDataMartModel.materialized,
    )
    for materialized in materialized_models:
        assert materialized._meta.app_label == 'edw_contracts'
    assert EntityModel.materialized is ContractEntity
    assert DataMartModel.materialized is DataMart
    assert not ForeignKeyBuilder._pending_mappings


def test_duplicate_root_entity_is_rejected():
    """Второй корень из BaseEntity должен упасть с ImproperlyConfigured."""
    script = '''
import django
django.setup()

from django.core.exceptions import ImproperlyConfigured
from edw.models.entity import BaseEntity
from edw.tests.contract.app.models import ContractEntity


def main():
    try:
        class SecondRoot(BaseEntity):
            class Meta:
                abstract = False

            objects = ContractEntity.objects

            @property
            def entity_name(self):
                return 'second'

            def get_absolute_url(self, request=None, format=None):
                return '/'
    except ImproperlyConfigured as error:
        print('DUPLICATE_REJECTED: {}'.format(error))
    else:
        print('DUPLICATE_ACCEPTED')


main()
'''
    env = dict(os.environ)
    env['DJANGO_SETTINGS_MODULE'] = 'edw_contract_settings'
    env['PYTHONPATH'] = os.pathsep.join(
        [str(BACKEND_DIR)] + [part for part in env.get('PYTHONPATH', '').split(os.pathsep) if part]
    )
    completed = subprocess.run(
        [sys.executable, '-c', script],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    output = completed.stdout.decode('utf-8', 'replace')
    assert completed.returncode == 0, completed.stderr.decode('utf-8', 'replace')[-2000:]
    assert 'DUPLICATE_REJECTED' in output
    assert 'disallowed' in output
