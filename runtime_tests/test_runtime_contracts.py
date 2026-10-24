# -*- coding: utf-8 -*-
"""
E7: consumer-contract checks for the real InfLabs bulk API.

These are behavioural/structural assertions on EDW itself:

* validators speak the DRF 3.15+ context protocol (``requires_context`` +
  ``__call__(attrs, serializer)``), no mutable ``set_context`` state;
* every bulk list serializer overrides the provider's deliberately empty
  ``validate_bulk_create`` admission hook;
* the global-manager upsert helper is gone from the product;
* bulk admission resolves a single ``db_for_write`` alias, not the read router;
* the base collection-DELETE policy is default-deny.
"""
from __future__ import unicode_literals

import inspect
from unittest import mock

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework_bulk.serializers import BulkListSerializer

from edw.models import rest as rest_models
from edw.models.defaults.term import Term
from edw.rest.serializers.bulk import ScopedBulkAdmissionMixin
from edw.rest.serializers.data_mart import (
    DataMartBulkListSerializer,
    DataMartCommonSerializer,
    DataMartValidator,
)
from edw.rest.serializers.entity import (
    EntityBulkListSerializer,
    EntityDetailSerializerBase,
    EntityValidator,
)
from edw.rest.serializers.term import (
    DataMartBulkListSerializer as TermBulkListSerializer,
    TermDetailSerializer,
    TermValidator,
)
from edw.rest.viewsets import BulkDestroyPolicyMixin
from edw.views.term import TermViewSet

pytestmark = pytest.mark.django_db


def test_validators_use_the_drf_context_protocol():
    for validator_class in (TermValidator, EntityValidator, DataMartValidator):
        assert validator_class.requires_context is True
        assert not hasattr(validator_class, 'set_context'), validator_class.__name__
        parameters = list(inspect.signature(validator_class.__call__).parameters)
        assert parameters == ['self', 'attrs', 'serializer'], (
            validator_class.__name__, parameters
        )


def test_admission_hook_is_not_the_provider_default():
    assert (
        ScopedBulkAdmissionMixin.validate_bulk_create
        is not BulkListSerializer.validate_bulk_create
    )
    for serializer_class in (
        TermBulkListSerializer,
        DataMartBulkListSerializer,
        EntityBulkListSerializer,
    ):
        assert issubclass(serializer_class, ScopedBulkAdmissionMixin)
        assert serializer_class.validate_bulk_create is (
            ScopedBulkAdmissionMixin.validate_bulk_create
        )
        assert serializer_class.bulk_admission_new_required_fields, serializer_class


def test_global_manager_upsert_helper_is_removed():
    assert not hasattr(rest_models, 'UpdateOrCreateSerializerMixin')
    for serializer_class in (
        TermDetailSerializer,
        DataMartCommonSerializer,
        EntityDetailSerializerBase,
    ):
        source = inspect.getsource(serializer_class.create)
        assert '_update_or_create_instance' not in source
        assert 'objects.get(' not in source


def test_bulk_admission_uses_one_write_alias():
    view = TermViewSet()
    view.request = Request(APIRequestFactory().get('/'))
    serializer = TermDetailSerializer(
        many=True, context={'view': view, 'request': view.request}
    )
    model = serializer.get_admission_model()
    with mock.patch('django.db.router.db_for_write', return_value='default') as write_router, \
            mock.patch('django.db.router.db_for_read', return_value='replica'):
        assert serializer.get_write_alias(model) == 'default'
        write_router.assert_called()
        queryset = serializer.get_admission_queryset('default')
        assert queryset._db == 'default'
        assert Term.objects.all()._db is None


def test_base_collection_delete_policy_is_default_deny():
    class _BasePolicyView(BulkDestroyPolicyMixin):
        pass

    view = _BasePolicyView()
    view.request = APIRequestFactory().delete('/')
    view.kwargs = {}
    assert view.allow_bulk_destroy(None, Term.objects.none()) is False
