# -*- coding: utf-8 -*-
"""
E11/R6: post-suite evidence recorded in the *test interpreter*.

The gate installs the freshly built wheel into a clean environment and runs the
product suites there.  A pre-suite check of the installed payload is not enough:
a test process can import another ``edw`` from ``sys.path``, a stub namespace,
or a mutated payload.  This module is called from ``pytest_sessionfinish`` (the
same interpreter that executed the tests, after the whole suite) and records:

* the actual imported ``edw`` origin and ``django-edw`` version;
* a full dist-info ``RECORD`` hash check of the installed candidate;
* the origins of the real provider namespaces and their distribution metadata
  bytes;
* absence of the E1 stub path/``edw_contract_compat`` and of any ``edw`` module
  imported from outside the installed site;
* the interpreter optimization flag and the suite exit status.

The runner refuses the run when the file is missing, malformed, or contradicts
the environment (see ``check_safety_env.py post-suite``).
"""
from __future__ import unicode_literals

import base64
import csv
import hashlib
import importlib
import importlib.util
import json
import os
import pathlib
import site
import sys

REAL_NAMESPACES = (
    'bitfield',
    'rest_framework_bulk',
    'rest_framework_filters',
    'rest_framework_recursive',
)

PROVIDER_DISTRIBUTIONS = {
    'bitfield': 'django-bitfield',
    'rest_framework_bulk': 'djangorestframework-bulk',
    'rest_framework_filters': 'djangorestframework-filters',
    'rest_framework_recursive': 'djangorestframework-recursive',
}

STUB_MODULE_PREFIX = 'edw.tests.contract.stubs'
STUB_PATH_SUFFIX = '/edw/tests/contract/stubs'


def _file_sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _record_check(site_dir):
    report = {
        'record_entries': 0,
        'record_checked': 0,
        'record_missing': [],
        'record_mismatch': [],
        'dist_info_dirs': [],
        'dist_version': None,
    }
    import importlib.metadata as metadata

    try:
        report['dist_version'] = metadata.version('django-edw')
    except Exception as exc:  # pragma: no cover - evidence must stay visible
        report['dist_version'] = 'ERROR: {!r}'.format(exc)
    dist_infos = sorted(site_dir.glob('django_edw-*.dist-info'))
    report['dist_info_dirs'] = [str(path) for path in dist_infos]
    for dist_info in dist_infos:
        record = dist_info / 'RECORD'
        if not record.is_file():
            report['record_missing'].append(str(record))
            continue
        with record.open(newline='', encoding='utf-8') as handle:
            for row in csv.reader(handle):
                if not row or len(row) < 2 or not row[1]:
                    continue
                name, hash_field = row[0], row[1]
                report['record_entries'] += 1
                algorithm, expected = hash_field.split('=', 1)
                target = site_dir / name
                if not target.is_file():
                    report['record_missing'].append(name)
                    continue
                actual = base64.urlsafe_b64encode(
                    hashlib.sha256(target.read_bytes()).digest()).rstrip(b'=').decode()
                report['record_checked'] += 1
                if algorithm != 'sha256' or actual != expected:
                    report['record_mismatch'].append(name)
    report['record_missing'] = report['record_missing'][:20]
    report['record_mismatch'] = report['record_mismatch'][:20]
    return report


def build_evidence():
    """Collect the post-suite facts in the current interpreter."""
    site_dir = pathlib.Path(site.getsitepackages()[0]).resolve()
    report = {
        'interpreter': sys.executable,
        'prefix': sys.prefix,
        'site': str(site_dir),
        'python': sys.version.split()[0],
        'optimize': int(sys.flags.optimize),
        'cwd': os.getcwd(),
        'settings': os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown'),
        'edw_package_imported': 'edw' in sys.modules,
        'edw_file': None,
        'edw_modules_outside_site': [],
        'edw_contract_compat_importable': None,
        'active_stub_modules': sorted(
            name for name in sys.modules if name.startswith(STUB_MODULE_PREFIX)
        ),
        'stub_sys_path_entries': [
            entry for entry in sys.path
            if str(entry).replace('\\\\', '/').rstrip('/').endswith(STUB_PATH_SUFFIX)
        ],
        'namespaces': {},
        'providers': {},
        'sys_path': [str(entry) for entry in sys.path],
    }
    report.update(_record_check(site_dir))

    edw = importlib.import_module('edw')
    edw_path = pathlib.Path(edw.__file__).resolve()
    report['edw_file'] = str(edw_path)
    outside = []
    for name, module in sorted(sys.modules.items()):
        if name != 'edw' and not name.startswith('edw.'):
            continue
        module_file = getattr(module, '__file__', None)
        if module_file is None:
            continue
        resolved = pathlib.Path(module_file).resolve()
        if site_dir not in resolved.parents:
            outside.append({'module': name, 'file': str(resolved)})
    report['edw_modules_outside_site'] = outside
    report['edw_contract_compat_importable'] = importlib.util.find_spec(
        'edw_contract_compat') is not None

    for module_name in REAL_NAMESPACES:
        module = sys.modules.get(module_name)
        if module is None:
            report['namespaces'][module_name] = None
            continue
        report['namespaces'][module_name] = {
            'file': getattr(module, '__file__', None),
            'package': getattr(module, '__package__', None),
        }
    for module_name, distribution in PROVIDER_DISTRIBUTIONS.items():
        entry = {'distribution': distribution, 'version': None, 'metadata_sha256': None,
                 'record_sha256': None, 'dist_info': None}
        try:
            import importlib.metadata as metadata
            dist = metadata.distribution(distribution)
            entry['version'] = dist.version
            init_path = pathlib.Path(dist.locate_file(module_name + '/__init__.py')).resolve()
            entry['module_sha256'] = _file_sha256(init_path)
            dist_info = pathlib.Path(init_path).parent.parent / (
                '{}-{}.dist-info'.format(
                    distribution.replace('-', '_'), dist.version))
            candidates = list(
                pathlib.Path(init_path).parent.parent.glob(
                    '{}*.dist-info'.format(distribution.replace('-', '_')))
            )
            if len(candidates) != 1:
                candidates = list(
                    pathlib.Path(init_path).parent.parent.glob(
                        '{}*.dist-info'.format(distribution.lower().replace('-', '_'))))
            if len(candidates) != 1:
                entry['dist_info'] = 'ambiguous: {}'.format([str(p) for p in candidates])
            else:
                entry['dist_info'] = str(candidates[0])
                for name in ('METADATA', 'RECORD'):
                    path = candidates[0] / name
                    entry['{}_sha256'.format(name.lower())] = (
                        _file_sha256(path) if path.is_file() else None)
        except Exception as exc:  # pragma: no cover - evidence stays visible
            entry['error'] = '{!r}'.format(exc)
        report['providers'][module_name] = entry
    return report


def write_post_suite_evidence(exitstatus, evidence_dir=None):
    """Write the post-suite JSON; never raises into the test session."""
    directory = evidence_dir or os.environ.get('EDW_SAFETY_EVIDENCE_DIR')
    if not directory:
        return None
    settings = os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown')
    target = pathlib.Path(directory) / 'post-suite-{}.json'.format(
        str(settings).replace('.', '_'))
    try:
        report = build_evidence()
    except Exception as exc:  # pragma: no cover - evidence stays visible
        report = {'error': '{!r}'.format(exc)}
    report['exitstatus'] = int(exitstatus)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n',
                          encoding='utf-8')
    except Exception:  # pragma: no cover - the runner reports the missing file
        return None
    return str(target)
