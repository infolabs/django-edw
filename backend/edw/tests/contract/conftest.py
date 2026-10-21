# -*- coding: utf-8 -*-
"""E1: общие фикстуры характеризационных тестов django-edw."""
from __future__ import unicode_literals

from django.core.cache import cache
from edw.models.data_mart import DataMartModel
from edw.models.defaults.term import Term
from edw.models.entity import EntityModel
import pytest


@pytest.fixture(autouse=True)
def reset_edw_caches():
    """Сбрасывает кэши EDW между тестами (locmem + class-level кэши)."""
    cache.clear()
    EntityModel._entities_types_cache = None
    EntityModel._content_type_cache = {}
    if hasattr(DataMartModel, '_base_entity_model_cache'):
        DataMartModel._base_entity_model_cache = None
    yield
    cache.clear()
    EntityModel._entities_types_cache = None


@pytest.fixture
def entity_types():
    """
    Материализует термин-дерево типов Entity (контракт validate_term_model).

    В тестовой БД AppConfig.ready() ядра пропускает этот шаг (см. app/apps.py),
    поэтому дерево создаётся явно — как это делает ready() в рабочем процессе.
    """
    EntityModel._validate_term_model_cache = {}
    root = EntityModel.materialized
    for clazz in [root] + list(root.get_all_subclasses()):
        clazz.validate_term_model()
    return {
        'root': Term.objects.get(slug=root.__name__.lower()),
        'child': Term.objects.get(slug='contractentitychild'),
    }
