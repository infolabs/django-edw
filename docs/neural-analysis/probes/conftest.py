# -*- coding: utf-8 -*-
"""E12.residualcheck: independent check harness.

Deliberately does not import the author's ``runtime_tests/conftest.py`` (no
author fixtures, no author post-suite writer).  Only the product package and
the synthetic contract app/models shipped in the candidate wheel are used.
"""
from __future__ import unicode_literals

import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e12_settings')

EVIDENCE_DIR = pathlib.Path(
    os.environ.get('E12_EVIDENCE_DIR',
                   str(HERE.parent / 'evidence'))).resolve()


@pytest.fixture(autouse=True)
def reset_check_state():
    import e12_routers
    import e12_views
    from django.core.cache import cache
    from edw.models.data_mart import DataMartModel
    from edw.models.entity import EntityModel

    e12_routers.reset_all()
    e12_views.reset_state()
    cache.clear()
    EntityModel._entities_types_cache = None
    EntityModel._content_type_cache = {}
    if hasattr(DataMartModel, '_base_entity_model_cache'):
        DataMartModel._base_entity_model_cache = None
    yield
    e12_routers.reset_all()
    e12_views.reset_state()
    cache.clear()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def superuser(db):
    from django.contrib.auth.models import User
    return User.objects.create_superuser(
        username='e12-root', email='e12-root@example.invalid', password='not-a-secret')


@pytest.fixture
def operator(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


@pytest.fixture
def entity_types(db):
    from edw.models.defaults.term import Term
    from edw.models.entity import EntityModel

    EntityModel._validate_term_model_cache = {}
    root = EntityModel.materialized
    for clazz in [root] + list(root.get_all_subclasses()):
        clazz.validate_term_model()
    return {
        'root': Term.objects.get(slug=root.__name__.lower()),
        'child': Term.objects.get(slug='contractentitychild'),
    }


def _sha256(path):
    import hashlib
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _post_suite_evidence(exitstatus):
    """Same-interpreter post-suite evidence (R6-G1 control)."""
    import base64
    import importlib.metadata as metadata
    import sysconfig

    site = pathlib.Path(sysconfig.get_paths()['purelib']).resolve()
    pre = json.loads((EVIDENCE_DIR / 'install-check.json').read_text())
    reasons = []

    def check(condition, reason):
        if not condition:
            reasons.append(reason)

    check(int(sys.flags.optimize) == 0, 'optimized interpreter')
    check(exitstatus == 0, 'suite exit status {}'.format(exitstatus))

    import edw
    edw_file = pathlib.Path(edw.__file__).resolve()
    check(site in edw_file.parents, 'edw origin outside site: {}'.format(edw_file))

    dist = metadata.distribution('django-edw')
    dist_info = pathlib.Path(dist._path).resolve()
    record_entries = record_checked = 0
    record_missing = []
    record_mismatch = []
    for line in (dist_info / 'RECORD').read_text(encoding='utf-8').splitlines():
        row = line.split(',')
        if len(row) < 2 or not row[1]:
            continue
        record_entries += 1
        target = site / row[0]
        if not target.is_file():
            record_missing.append(row[0])
            continue
        algorithm, expected = row[1].split('=', 1)
        actual = base64.urlsafe_b64encode(
            __import__('hashlib').sha256(target.read_bytes()).digest()).rstrip(b'=').decode()
        record_checked += 1
        if algorithm != 'sha256' or actual != expected:
            record_mismatch.append(row[0])
    check(record_entries == pre['record_entries'],
          'RECORD entries changed: {} != {}'.format(record_entries, pre['record_entries']))
    check(record_checked == record_entries,
          'RECORD not fully verified: {} != {}'.format(record_checked, record_entries))
    check(not record_missing, 'RECORD files missing: {}'.format(record_missing[:5]))
    check(not record_mismatch, 'RECORD mismatches: {}'.format(record_mismatch[:5]))

    providers = {}
    for module_name, distribution in (
            ('bitfield', 'django-bitfield'),
            ('rest_framework_bulk', 'djangorestframework-bulk'),
            ('rest_framework_filters', 'djangorestframework-filters'),
            ('rest_framework_recursive', 'djangorestframework-recursive')):
        module = __import__(module_name)
        module_file = pathlib.Path(module.__file__).resolve()
        check(site in module_file.parents,
              '{} origin outside site: {}'.format(module_name, module_file))
        candidates = sorted(site.glob('{}*.dist-info'.format(
            distribution.replace('-', '_'))))
        check(len(candidates) == 1,
              'ambiguous metadata for {}'.format(distribution))
        providers[module_name] = {
            'version': metadata.version(distribution),
            'module_sha256': _sha256(module_file),
            'record_sha256': _sha256(candidates[0] / 'RECORD') if candidates else None,
            'metadata_sha256': _sha256(candidates[0] / 'METADATA') if candidates else None,
        }
        pre_provider = pre['providers'].get(module_name) or {}
        check(providers[module_name]['module_sha256'] == pre_provider.get('module_sha256'),
              '{} module bytes changed'.format(module_name))
        check(providers[module_name]['record_sha256'] == pre_provider.get('record_sha256'),
              '{} RECORD bytes changed'.format(module_name))

    try:
        import edw_contract_compat  # noqa: F401
        compat_importable = True
    except Exception:
        compat_importable = False
    check(not compat_importable, 'edw_contract_compat stub namespace is importable')
    stub_paths = [entry for entry in sys.path if 'stubs' in pathlib.Path(entry).parts]
    check(not stub_paths, 'stub sys.path entries present: {}'.format(stub_paths))
    outside = sorted(
        name for name, module in list(sys.modules.items())
        if name == 'edw' or name.startswith('edw.')
        if getattr(module, '__file__', None)
        and site not in pathlib.Path(module.__file__).resolve().parents)

    report = {
        'schema': 'edw-modernize/e12-check/post-suite/1',
        'ok': not reasons,
        'reasons': reasons,
        'exitstatus': exitstatus,
        'optimize': int(sys.flags.optimize),
        'python': sys.executable,
        'site': str(site),
        'settings': os.environ.get('DJANGO_SETTINGS_MODULE'),
        'edw_file': str(edw_file),
        'dist_version': dist.version,
        'record_entries': record_entries,
        'record_checked': record_checked,
        'record_missing': record_missing,
        'record_mismatch': record_mismatch,
        'providers': providers,
        'edw_contract_compat_importable': compat_importable,
        'stub_sys_path_entries': stub_paths,
        'edw_modules_outside_site': outside,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
    }
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / 'post-suite-session.json').write_text(
        json.dumps(report, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    return report


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    try:
        _post_suite_evidence(int(exitstatus))
    except Exception as exc:  # evidence failure must be visible, not silent
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        (EVIDENCE_DIR / 'post-suite-session.json').write_text(
            json.dumps({'ok': False, 'error': repr(exc)}, indent=1) + '\n',
            encoding='utf-8')
