# -*- coding: utf-8 -*-
"""
E1: контракт REST-слоя: RESTMeta моделей, сериализаторы Entity / DataMart /
Term (наборы полей и эталонные представления), парсинг rel-ключей фильтра.
"""
from __future__ import unicode_literals

import pytest
from rest_framework.test import APIRequestFactory

from edw.models.defaults.term import Term
from edw.tests.contract.app.models import ContractEntity, ContractEntityChild, DataMart
from edw.rest.filters.entity import EntityFilter
from edw.rest.serializers.data_mart import DataMartCommonSerializer
from edw.rest.serializers.entity import EntityDetailSerializer, EntitySummarySerializer
from edw.rest.serializers.term import TermDetailSerializer, TermSummarySerializer

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_request():
    return APIRequestFactory().get('/')


def test_rest_meta_contract():
    assert ContractEntity._rest_meta.lookup_fields == ('id',)
    assert ContractEntity._rest_meta.exclude == ['name']
    assert ContractEntityChild._rest_meta.exclude == ['name', 'code']
    assert DataMart._rest_meta.lookup_fields == ('id', 'slug')


def test_entity_summary_serializer(entity_types, api_request):
    entity = ContractEntity.objects.create(name='Alpha')
    data = EntitySummarySerializer(entity, context={'request': api_request}).data

    assert set(data) == {
        'id', 'entity_name', 'entity_url', 'entity_model',
        'short_characteristics', 'short_marks', 'media', 'extra',
    }
    assert data['id'] == entity.pk
    assert data['entity_name'] == 'Alpha'
    assert data['entity_model'] == 'contractentity'
    assert data['entity_url'] == 'http://testserver/contractentity/{}/'.format(entity.pk)
    assert data['short_characteristics'] == []
    assert data['short_marks'] == []
    assert data['extra'] is None
    assert data['media'].startswith('<!-- no such template:')
    assert 'summary-contractentity-media.html' in data['media']


def test_entity_detail_serializer(entity_types, api_request):
    entity = ContractEntity.objects.create(name='Alpha', description='Desc')
    data = EntityDetailSerializer(entity, context={'request': api_request}).data

    assert set(data) == {
        'id', 'entity_model', 'entity_name', 'active', 'terms_ids',
        'characteristics', 'marks', 'related_data_marts', 'extra', 'media',
        'created_at', 'updated_at', 'description',
    }
    assert data['entity_name'] == 'Alpha'
    assert data['description'] == 'Desc'
    assert data['active'] is True
    assert data['terms_ids'] == [entity_types['root'].pk]
    assert data['characteristics'] == []
    assert data['marks'] == []
    assert data['related_data_marts'] == []
    assert data['media'].startswith('<!-- no such template:')
    assert 'detail-contractentity-media.html' in data['media']


def test_datamart_common_serializer(api_request):
    data_mart = DataMart.objects.create(name='DM', slug='dm', description='D')
    data = DataMartCommonSerializer(data_mart, context={'request': api_request}).data

    assert set(data) == {
        'id', 'name', 'parent_id', 'slug', 'path', 'active', 'description',
        'data_mart_model', 'data_mart_url', 'is_leaf', 'short_description',
        'created_at', 'updated_at', 'ordering', 'view_component', 'limit',
        'view_class', 'system_flags', 'lft', 'rght', 'tree_id', 'level',
        'polymorphic_ctype', 'parent', '_relations', 'terms',
    }
    assert data['name'] == 'DM'
    assert data['slug'] == 'dm'
    assert data['path'] == 'dm'
    assert data['data_mart_model'] == 'datamart'
    assert data['data_mart_url'] == 'http://testserver/datamart/{}/'.format(data_mart.pk)
    assert data['is_leaf'] is True
    assert data['short_description'] == 'D'
    assert data['ordering'] == '-created_at'
    assert data['view_component'] == 'list'
    assert data['system_flags'] == 0
    assert data['level'] == 0
    assert data['parent'] is None
    assert data['terms'] == []
    assert data['_relations'] == []


def test_term_detail_serializer(api_request):
    term = Term.objects.create(name='Root', slug='root')
    data = TermDetailSerializer(term, context={'request': api_request}).data

    assert set(data) == {
        'id', 'parent_id', 'name', 'slug', 'path', 'semantic_rule',
        'specification_mode', 'url', 'active', 'description', 'view_class',
        'created_at', 'updated_at', 'level', 'attributes', 'is_leaf',
    }
    assert data['name'] == 'Root'
    assert data['slug'] == 'root'
    assert data['path'] == 'root'
    assert data['semantic_rule'] == Term.OR_RULE
    assert data['specification_mode'] == Term.STANDARD_SPECIFICATION
    assert data['url'] == 'http://testserver/term/{}/'.format(term.pk)
    assert data['level'] == 0
    assert data['attributes'] == 0
    assert data['is_leaf'] is True


def test_term_summary_serializer(api_request):
    term = Term.objects.create(name='Root', slug='root', description='Some description')
    data = TermSummarySerializer(term, context={'request': api_request}).data

    assert set(data) == {
        'id', 'parent_id', 'name', 'slug', 'semantic_rule',
        'specification_mode', 'url', 'active', 'view_class', 'attributes',
        'is_leaf', 'short_description',
    }
    assert data['short_description'] == 'Some description'
    assert data['is_leaf'] is True


def test_entity_filter_separate_rel_by_key():
    assert EntityFilter.separate_rel_by_key('10b', 'b') == 10
    assert EntityFilter.separate_rel_by_key('10f', 'f') == 10
    assert EntityFilter.separate_rel_by_key('10r', 'r') == 10
    assert EntityFilter.separate_rel_by_key('10', 'b') is None
    assert EntityFilter.separate_rel_by_key('7f', 'b') is None
