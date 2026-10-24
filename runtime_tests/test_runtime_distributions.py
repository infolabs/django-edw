# -*- coding: utf-8 -*-
"""
E7: the real runtime must resolve the accepted matrix and the four namespaces
from installed distributions, never from the E1 contract stubs and never
through ``edw_contract_compat``.
"""
from __future__ import unicode_literals

import importlib
import importlib.util
import pathlib
import sys
from importlib import metadata

import pytest


MATRIX_VERSIONS = {
    'Django': '5.2.18',
    'djangorestframework': '3.18.3',
    'django-bitfield': '2.4.0',
    'djangorestframework-bulk': '0.3.0a1',
    'django-filter': '26.2',
    'djangorestframework-filters': '1.0.0.dev2',
    'djangorestframework-recursive': '0.1.2',
}

REAL_NAMESPACES = {
    'bitfield': 'django-bitfield',
    'rest_framework_bulk': 'djangorestframework-bulk',
    'rest_framework_filters': 'djangorestframework-filters',
    'rest_framework_recursive': 'djangorestframework-recursive',
}


def _site_packages():
    import site

    paths = [pathlib.Path(path).resolve() for path in site.getsitepackages()]
    paths.append(pathlib.Path(sys.prefix, 'lib').resolve())
    return paths


def test_matrix_versions_are_exact():
    for distribution, expected in MATRIX_VERSIONS.items():
        installed = metadata.version(distribution)
        assert installed == expected, '{}: {} != {}'.format(distribution, installed, expected)


def test_four_namespaces_resolve_to_real_distributions():
    for module_name, distribution in REAL_NAMESPACES.items():
        module = importlib.import_module(module_name)
        module_path = pathlib.Path(module.__file__).resolve()
        assert '/stubs/' not in module_path.as_posix(), (
            '{} imported from the E1 stub tree: {}'.format(module_name, module_path)
        )
        dist = metadata.distribution(distribution)
        dist_file = pathlib.Path(dist.locate_file(module_name + '/__init__.py')).resolve()
        assert module_path == dist_file, (
            '{} resolved outside {}: {} != {}'.format(
                module_name, distribution, module_path, dist_file
            )
        )
        assert dist.version == MATRIX_VERSIONS[distribution]


def test_no_stub_path_is_active():
    stub_suffix = '/edw/tests/contract/stubs'
    active = [entry for entry in sys.path if str(entry).replace('\\', '/').endswith(stub_suffix)]
    assert active == [], 'E1 stub directory is on sys.path: {}'.format(active)
    assert importlib.util.find_spec('edw_contract_compat') is None, (
        'edw_contract_compat is importable in the real runtime'
    )
    assert 'edw_contract_compat' not in sys.modules


def test_stub_modules_are_not_active():
    active = []
    for name, module in list(sys.modules.items()):
        if name.startswith('edw.tests.contract.stubs'):
            active.append(name)
        if name in REAL_NAMESPACES and module is not None:
            module_file = getattr(module, '__file__', '') or ''
            if '/stubs/' in module_file.replace('\\', '/'):
                active.append(name)
    assert active == [], 'active stub modules: {}'.format(active)


def test_edw_is_imported_from_the_installed_wheel():
    import edw

    edw_path = pathlib.Path(edw.__file__).resolve()
    assert '/stubs/' not in edw_path.as_posix()
    assert edw_path.parent.name == 'edw'
    assert 'site-packages' in edw_path.parts, (
        'edw is not imported from the installed wheel: {}'.format(edw_path)
    )
    assert metadata.version('django-edw') == '0.2.0'
