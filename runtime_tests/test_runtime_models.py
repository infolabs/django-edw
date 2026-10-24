# -*- coding: utf-8 -*-
"""
E7: BitField and RecursiveField are provided by the installed real packages,
and the synthetic application materializes exactly one root Entity.
"""
from __future__ import unicode_literals

import pytest

from edw.deferred import ForeignKeyBuilder
from edw.models.data_mart import DataMartModel
from edw.models.entity import BaseEntity, EntityModel
from edw.models.term import TermModel
from edw.rest.serializers.data_mart import DataMartTreeSerializer
from edw.rest.serializers.term import TermTreeSerializer
from edw.tests.contract.app.models import ContractEntity


def test_bitfield_is_the_real_package():
    import bitfield

    assert bitfield.__file__.replace('\\', '/').endswith('/bitfield/__init__.py')
    assert '/stubs/' not in bitfield.__file__.replace('\\', '/')
    field = TermModel.attributes
    assert field.__class__.__module__.split('.')[0] == 'bitfield'
    flag = TermModel.attributes.is_characteristic
    assert int(flag) == 1


def test_recursive_field_is_the_real_package():
    import rest_framework_recursive

    assert rest_framework_recursive.__file__.replace('\\', '/').endswith(
        'rest_framework_recursive/__init__.py'
    )
    assert '/stubs/' not in rest_framework_recursive.__file__.replace('\\', '/')

    field = TermTreeSerializer().fields['children'].child
    assert isinstance(field, rest_framework_recursive.fields.RecursiveField)
    data_mart_field = DataMartTreeSerializer().fields['children'].child
    assert isinstance(data_mart_field, rest_framework_recursive.fields.RecursiveField)


def test_single_root_entity():
    assert BaseEntity._meta.abstract is True
    assert ContractEntity._meta.abstract is False
    assert EntityModel.materialized is ContractEntity
    assert BaseEntity._materialized_model is ContractEntity
    roots = [
        name for abstract, name in ForeignKeyBuilder._materialized_models.items()
        if abstract == 'BaseEntity'
    ]
    assert roots == ['ContractEntity']
    assert DataMartModel.materialized._meta.app_label == 'edw_contracts'
    assert not ForeignKeyBuilder._pending_mappings
