# -*- coding: utf-8 -*-
"""
E4: целевая матрица зависимостей G0.1 и проверка pyproject.toml.

Матрица G0.1 из ``edw-inventory.json`` фиксирует офлайн-стек, на котором
проверяются контракты EDW:

====================================  ============
распределение                         версия
====================================  ============
Django                                5.2.18 LTS
djangorestframework                   3.18.3
django-mptt                           0.20.0
django-polymorphic                    4.11.7
django-select2                        8.4.8
django-filer                          3.6.0
django-fsm-2                          4.2.4
====================================  ============

Верхние границы в ``pyproject.toml`` должны исключать следующую линию,
которая ещё не проходила характеризацию: Django 5.3, DRF 3.19,
django-mptt 0.21, django-polymorphic 4.12, django-select2 8.5,
django-filer 3.7, django-fsm-2 4.3. Модуль не импортирует Django: его
можно вызывать до ``django.setup()`` из scripts/check.sh.
"""
from __future__ import unicode_literals

import os
from pathlib import Path
import tomllib

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

try:
    from importlib import metadata
except ImportError:  # pragma: no cover - Python 3.7 и старше
    import importlib_metadata as metadata


#: Распределение -> исключающая версия следующей непроверенной линии.
TARGET_UPPER_BOUNDS = {
    'django': '5.3',
    'djangorestframework': '3.19',
    'django-mptt': '0.21',
    'django-polymorphic': '4.12',
    'django-select2': '8.5',
    'django-filer': '3.7',
    'django-fsm-2': '4.3',
}

#: Импортируемый модуль для каждой зависимости матрицы (адаптер).
ADAPTER_MODULES = {
    'django': 'django',
    'djangorestframework': 'rest_framework',
    'django-mptt': 'mptt',
    'django-polymorphic': 'polymorphic',
    'django-select2': 'django_select2',
    'django-filer': 'filer',
    'django-fsm-2': 'django_fsm',
}

#: Заменённые зависимости: распределение -> чем заменено.
REPLACED_DISTRIBUTIONS = {
    'django-fsm': 'django-fsm-2',
}


def find_project_root(start=None):
    """Ищет каталог с pyproject.toml вверх от пути запуска."""
    override = os.environ.get('EDW_REPO_ROOT')
    if override:
        root = Path(override).resolve()
        if (root / 'pyproject.toml').is_file():
            return root
        raise LookupError('EDW_REPO_ROOT={} не содержит pyproject.toml'.format(override))

    bases = []
    if start is not None:
        bases.append(Path(start).resolve())
    bases.append(Path.cwd())
    bases.append(Path(__file__).resolve())

    for base in bases:
        for candidate in (base, *base.parents):
            if (candidate / 'pyproject.toml').is_file():
                return candidate
    raise LookupError('не найден pyproject.toml (задайте EDW_REPO_ROOT)')


def load_declared_requirements(project_root=None):
    """Возвращает список Requirement из [project].dependencies."""
    root = find_project_root(project_root)
    with (root / 'pyproject.toml').open('rb') as fh:
        data = tomllib.load(fh)
    try:
        raw = data['project']['dependencies']
    except KeyError:
        raise LookupError('pyproject.toml без [project].dependencies')
    requirements = []
    for item in raw:
        try:
            requirements.append(Requirement(item))
        except InvalidRequirement as exc:
            raise InvalidRequirement('некорректная зависимость {!r}: {}'.format(item, exc))
    return requirements


def declared_by_name(requirements):
    """Раскладывает требования по каноничным именам распределений."""
    return {canonicalize_name(req.name): req for req in requirements}


def installed_version(distribution):
    """Версия установленного распределения или None."""
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def check_matrix(project_root=None):
    """
    Сверяет pyproject.toml с матрицей G0.1 и установленным офлайн-стеком.

    :return: (errors, report) - список ошибок и строки отчёта.
    """
    errors = []
    report = []
    declared = declared_by_name(load_declared_requirements(project_root))

    for name, replaced_by in sorted(REPLACED_DISTRIBUTIONS.items()):
        if name in declared:
            errors.append(
                '{} объявлен в pyproject.toml, матрица G0.1 требует {}'.format(name, replaced_by)
            )

    for name, forbidden in sorted(TARGET_UPPER_BOUNDS.items()):
        requirement = declared.get(name)
        if requirement is None:
            errors.append('{} отсутствует в [project].dependencies'.format(name))
            continue

        if not requirement.specifier.contains(forbidden):
            report.append('{} {} исключает {}'.format(name, requirement.specifier, forbidden))
        else:
            errors.append(
                '{} {} допускает {}: верхняя граница не поднята по матрице G0.1'.format(
                    name, requirement.specifier or '(без границ)', forbidden
                )
            )

        version = installed_version(name)
        if version is None:
            errors.append('{} не установлен в текущем окружении'.format(name))
            continue
        try:
            parsed = Version(version)
        except InvalidVersion:
            errors.append('{}: некорректная версия {!r}'.format(name, version))
            continue
        if requirement.specifier and parsed not in requirement.specifier:
            errors.append(
                '{} {} не попадает в объявленный диапазон {}'.format(
                    name, version, requirement.specifier
                )
            )
        else:
            report.append('{} {} в диапазоне {}'.format(name, version, requirement.specifier or 'any'))

    return errors, report


def main():
    """Точка входа для scripts/check.sh: печатает отчёт, код 1 при ошибках."""
    errors, report = check_matrix()
    for line in report:
        print('  {}'.format(line))
    if errors:
        for error in errors:
            print('MATRIX FAIL: {}'.format(error))
        return 1
    print('  матрица G0.1: {} зависимостей согласованы'.format(len(TARGET_UPPER_BOUNDS)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
