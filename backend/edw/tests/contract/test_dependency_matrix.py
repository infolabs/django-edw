# -*- coding: utf-8 -*-
"""
E4: контракт целевой матрицы зависимостей G0.1 и адаптеров Django 5.2.

Матрица G0.1 (edw-inventory.json) фиксирует офлайн-стек 5.2/3.18/0.20/4.11/8.4/3.6/4.2.
Здесь проверяется, что pyproject.toml описывает именно её, а адаптеры
третьих библиотек (django-filter, django-mptt, django-fsm-2, filer)
работают на этом стеке.
"""
from __future__ import unicode_literals

import importlib

import pytest

from edw.tests.contract import matrix

ADAPTER_MODULES = (
    # django-filter адаптеры: name=..., CSV-виджет, парсинг soft-boolean.
    'edw.rest.filters.common',
    'edw.rest.filters.widgets',
    # django-filter + djangorestframework-filters backend.
    'edw.rest.filters.backends',
    # django-mptt адаптер поля дерева и ChoiceField полного пути.
    'edw.models.fields.tree',
    'edw.admin.mptt.fields',
    # django-fsm-2: модуль django_fsm импортируется из заменённого пакета.
    'django_fsm',
    'django_fsm.signals',
    # django-polymorphic и django-mptt: базовые модели адаптированы в edw.deferred.
    'polymorphic.models',
    'mptt.models',
    'edw.deferred',
)


def test_dependency_matrix_matches_g01():
    """Все зависимости матрицы объявлены и установленные версии в диапазоне."""
    errors, report = matrix.check_matrix()
    assert not errors, 'матрица G0.1 не согласована:\n{}'.format('\n'.join(errors))
    # Отчёт не пуст: каждая из зависимостей матрицы проверена.
    assert len(report) >= len(matrix.TARGET_UPPER_BOUNDS)


def test_dependency_matrix_rejects_unverified_lines():
    """Следующая непроверенная линия не должна входить в диапазон."""
    declared = matrix.declared_by_name(matrix.load_declared_requirements())
    for name, forbidden in matrix.TARGET_UPPER_BOUNDS.items():
        requirement = declared[name]
        assert not requirement.specifier.contains(forbidden), (
            '{} {} допускает непроверенную версию {}'.format(name, requirement.specifier, forbidden)
        )


def test_django_and_drf_upper_bounds_replaced():
    """Старые границы Django<4.0 и DRF без границы заменены матрицей G0.1."""
    declared = matrix.declared_by_name(matrix.load_declared_requirements())
    assert declared['django'].specifier.contains('5.2.18')
    assert declared['djangorestframework'].specifier.contains('3.18.3')
    assert not declared['django'].specifier.contains('4.0')


def test_django_fsm_is_replaced_by_django_fsm_2():
    """django-fsm прекращён; в зависимостях только поддерживаемый django-fsm-2."""
    names = set(matrix.declared_by_name(matrix.load_declared_requirements()))
    assert 'django-fsm-2' in names
    assert 'django-fsm' not in names
    import django_fsm

    assert django_fsm.__name__ == 'django_fsm'
    assert hasattr(django_fsm, 'RETURN_VALUE')
    assert hasattr(django_fsm, 'transition')
    assert hasattr(django_fsm, 'FSMField')


@pytest.mark.parametrize('module_name', ADAPTER_MODULES)
def test_dependency_adapter_importable(module_name):
    """Адаптер третьей библиотеки импортируется на стеке матрицы G0.1."""
    importlib.import_module(module_name)


def test_django_filter_name_kwarg_adapter():
    """
    edw.rest.filters.common возвращает django-filter аргумент ``name``.

    django-filter >= 2 убрал ``name`` (остался ``field_name``); адаптер должен
    переносить его без изменения поведения старых FilterSet'ов EDW.
    """
    from django_filters.filters import Filter

    from edw.rest.filters.common import parse_null_boolean

    filter_ = Filter(name='created_at', lookup_expr='exact')
    assert filter_.field_name == 'created_at'
    # Явный field_name приоритетнее ``name`` (совместимость со старым кодом).
    filter_ = Filter(name='created_at', field_name='updated_at', lookup_expr='exact')
    assert filter_.field_name == 'updated_at'
    assert parse_null_boolean('T') is True
    assert parse_null_boolean('0') is False
    assert parse_null_boolean('') is None


def test_django_filter_csv_widget_adapter():
    """CSVWidget адаптирует django_filters.widgets.CSVWidget к списковым значениям."""
    from edw.rest.filters.widgets import CSVWidget

    widget = CSVWidget()
    assert widget.value_from_datadict({'value': '1,2,3'}, {}, 'value') == ['1', '2', '3']
    assert widget.value_from_datadict({}, {}, 'value') is None


@pytest.mark.django_db
def test_mptt_full_path_choice_field_adapter():
    """
    django-mptt ChoiceField в Django 5.2: у ChoiceField больше нет _set_choices.

    Адаптер edw.admin.mptt.fields должен оставаться конструируемым и
    принимать присваивание choices через собственный сеттер.
    """
    from edw.admin.mptt.fields import FullPathTreeNodeChoiceField
    from edw.models.defaults.term import Term

    Term.objects.create(name='Root', slug='root')
    field = FullPathTreeNodeChoiceField(queryset=Term.objects.all(), required=False)
    sentinel = [('', '---------')]
    field.choices = sentinel
    assert field._choices == sentinel
    assert field.widget.choices == sentinel
