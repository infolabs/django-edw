#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E9/R6: offline helpers for the safety regression gate.

The gate must not run ``pip install`` and must not use the network.  Instead of
installing the freshly built wheel into a prepared environment, this module
materialises two fresh environments outside the clone:

``core``
    a ``python -m venv --without-pip`` environment that contains exactly the
    wheel's *mandatory* runtime dependency closure (``Requires-Dist`` without
    optional extras, transitively) plus the wheel payload itself.  This is the
    "fresh mandatory-only closure".

``gate``
    a venv containing the same wheel payload plus every distribution of the
    prepared source environment *except* the old ``django-edw`` payload and its
    metadata, so the declared test/build tooling is available while the product
    under test is only the new wheel.

Both environments are built by extracting the wheel archive and symlinking the
already verified distributions -- no installer, no package index, no network.

Subcommands::

    create-core --python PY --source-site DIR --wheel FILE --dest DIR [--json FILE]
    create-gate --python PY --source-site DIR --wheel FILE --dest DIR [--json FILE]
    verify     --site DIR --wheel FILE [--json FILE]
    junit      --file XML [--json FILE]
    smoke-info --site DIR

The script exits non-zero on any mismatch; missing or unreadable data is an
error, never a skip.
"""
from __future__ import unicode_literals

import argparse
import base64
import hashlib
import importlib.metadata as metadata
import json
import os
import pathlib
import subprocess
import sys
import zipfile

try:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    from packaging.version import Version
except ImportError:  # pragma: no cover - the build toolchain provides packaging
    Requirement = None


PRODUCT_PAYLOAD = ('edw', 'email_auth', 'social_extra')
PRODUCT_METADATA_PREFIX = 'django_edw-'


def _fail(message):
    raise SystemExit('SAFETY CLOSURE FAIL: {}'.format(message))


def _dist_index(path):
    index = {}
    for dist in metadata.distributions(path=[str(path)]):
        name = dist.metadata['Name']
        if not name:
            continue
        index[canonicalize_name(name)] = dist
    return index


def _wheel_metadata_text(wheel):
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith('.dist-info/METADATA')]
        if len(names) != 1:
            _fail('expected exactly one METADATA in the wheel, found {}'.format(names))
        return archive.read(names[0]).decode('utf-8')


def mandatory_requirements(metadata_text):
    """Mandatory (non-extra) requirements of the wheel."""
    for line in metadata_text.splitlines():
        if not line.startswith('Requires-Dist:'):
            continue
        requirement = Requirement(line.split(':', 1)[1].strip())
        if requirement.marker is None:
            yield requirement
            continue
        try:
            applies = requirement.marker.evaluate({'extra': ''})
        except Exception:
            applies = False
        if applies:
            yield requirement


def runtime_closure(metadata_text, dists):
    """Transitive mandatory closure of the wheel inside ``dists``."""
    closure = {}
    missing = []
    stack = [requirement.name for requirement in mandatory_requirements(metadata_text)]
    while stack:
        name = canonicalize_name(stack.pop())
        if name in closure:
            continue
        dist = dists.get(name)
        if dist is None:
            missing.append(name)
            continue
        closure[name] = dist
        for line in dist.requires or []:
            requirement = Requirement(line)
            if requirement.marker is not None:
                try:
                    if not requirement.marker.evaluate({'extra': ''}):
                        continue
                except Exception:
                    continue
            stack.append(requirement.name)
    return closure, missing


def _dist_top_levels(dist):
    tops = set()
    for entry in dist.files or []:
        parts = pathlib.PurePosixPath(str(entry).replace(os.sep, '/')).parts
        if not parts or parts[0] == '..':
            continue
        tops.add(parts[0])
    return tops


def _link_distribution(dest, dist, source_site):
    for top in _dist_top_levels(dist):
        source = pathlib.Path(source_site) / top
        target = pathlib.Path(dest) / top
        if not source.exists() or target.exists():
            continue
        os.symlink(os.path.abspath(str(source)), str(target))


def _create_venv(python, dest):
    subprocess.run(
        [python, '-m', 'venv', '--without-pip', str(dest)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    site = pathlib.Path(dest) / 'lib' / 'python{}.{}'.format(*sys.version_info[:2]) / 'site-packages'
    if not site.is_dir():
        _fail('fresh venv has no site-packages: {}'.format(site))
    return site


def _extract_wheel(wheel, site):
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(str(site))


def create_core(args):
    source_site = pathlib.Path(args.source_site)
    wheel = pathlib.Path(args.wheel)
    dest = pathlib.Path(args.dest)
    dists = _dist_index(source_site)
    text = _wheel_metadata_text(wheel)
    closure, missing = runtime_closure(text, dists)
    if missing:
        _fail('mandatory requirements are not installed in the source env: {}'.format(
            ', '.join(sorted(missing))))
    site = _create_venv(args.python, dest)
    for dist in closure.values():
        _link_distribution(site, dist, source_site)
    _extract_wheel(wheel, site)
    report = {
        'kind': 'core',
        'site': str(site),
        'required_distributions': sorted(closure),
        'linked_distributions': len(closure),
    }
    _write_json(args.json, report)
    print('  fresh core env: {} mandatory distributions + new wheel'.format(len(closure)))
    for name in sorted(closure):
        print('    {}=={}'.format(name, closure[name].version))
    return 0


def create_gate(args):
    source_site = pathlib.Path(args.source_site)
    wheel = pathlib.Path(args.wheel)
    dest = pathlib.Path(args.dest)
    site = _create_venv(args.python, dest)
    linked = 0
    for entry in sorted(source_site.iterdir()):
        name = entry.name
        if name in PRODUCT_PAYLOAD or name == '__pycache__':
            continue
        if name.startswith(PRODUCT_METADATA_PREFIX) and name.endswith('.dist-info'):
            # The reference wheel metadata may not shadow the new wheel.
            continue
        target = site / name
        if target.exists():
            continue
        os.symlink(os.path.abspath(str(entry)), str(target))
        linked += 1
    _extract_wheel(wheel, site)
    report = {'kind': 'gate', 'site': str(site), 'linked_entries': linked}
    _write_json(args.json, report)
    print('  fresh gate env: {} source entries (product payload excluded) + new wheel'.format(linked))
    return 0


def _verify_wheel_payload(site, wheel):
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        required = {'edw/__init__.py', 'email_auth/__init__.py', 'social_extra/__init__.py'}
        missing = sorted(required - set(names))
        if missing:
            _fail('wheel does not export packages: {}'.format(missing))
        legacy = [
            name for name in names
            if name.startswith('backend/') or name.startswith('sandbox/') or '/sandbox/' in name
        ]
        if legacy:
            _fail('legacy code leaked into the wheel: {}'.format(legacy[:5]))
        if 'edw/tests/contract/app/migrations/0001_initial.py' not in names:
            _fail('wheel lost the synthetic contract migrations')
        checked = 0
        for name in names:
            if name.endswith('/'):
                continue
            target = pathlib.Path(site) / name
            if not target.is_file():
                _fail('extracted wheel file is missing: {}'.format(name))
            if hashlib.sha256(archive.read(name)).hexdigest() != hashlib.sha256(
                    target.read_bytes()).hexdigest():
                _fail('extracted wheel file differs: {}'.format(name))
            checked += 1
        record_names = [name for name in names if name.endswith('.dist-info/RECORD')]
        if len(record_names) != 1:
            _fail('expected exactly one RECORD, found {}'.format(record_names))
        record_entries = 0
        for row in archive.read(record_names[0]).decode('utf-8').splitlines():
            if not row:
                continue
            parts = row.split(',')
            if len(parts) < 2 or not parts[1]:
                continue
            name, hash_field = parts[0], parts[1]
            algorithm, value = hash_field.split('=', 1)
            if algorithm != 'sha256':
                _fail('unexpected RECORD hash algorithm {}'.format(algorithm))
            target = pathlib.Path(site) / name
            if not target.is_file():
                _fail('RECORD entry is missing on disk: {}'.format(name))
            actual = base64.urlsafe_b64encode(
                hashlib.sha256(target.read_bytes()).digest()
            ).rstrip(b'=').decode('ascii')
            if actual != value:
                _fail('RECORD hash mismatch: {}'.format(name))
            record_entries += 1
    return {'wheel_files_checked': checked, 'record_entries_verified': record_entries}


def verify(args):
    site = pathlib.Path(args.site)
    wheel = pathlib.Path(args.wheel)
    dists = _dist_index(site)
    payload = _verify_wheel_payload(site, wheel)
    text = _wheel_metadata_text(wheel)

    import edw

    edw_path = pathlib.Path(edw.__file__).resolve()
    site_resolved = site.resolve()
    if site_resolved not in edw_path.parents:
        _fail('edw imported from outside the fresh wheel site: {}'.format(edw_path))
    if edw_path.parent.name != 'edw':
        _fail('unexpected edw package path: {}'.format(edw_path))

    edw_dist = dists.get('django-edw')
    if edw_dist is None:
        _fail('django-edw metadata is not visible in the fresh environment')
    if edw_dist.version != '0.2.0':
        _fail('unexpected django-edw version {}'.format(edw_dist.version))

    unsatisfied = []
    requirements = list(mandatory_requirements(text))
    for requirement in requirements:
        dist = dists.get(canonicalize_name(requirement.name))
        if dist is None:
            unsatisfied.append('{} (missing)'.format(requirement))
            continue
        if requirement.specifier and Version(dist.version) not in requirement.specifier:
            unsatisfied.append('{} (installed {})'.format(requirement, dist.version))
    if unsatisfied:
        _fail('mandatory requirements are not satisfied: {}'.format(unsatisfied))

    report = {
        'site': str(site_resolved),
        'edw_file': str(edw_path),
        'visible_distributions': len(dists),
        'mandatory_requirements': len(requirements),
        'unsatisfied': unsatisfied,
    }
    report.update(payload)
    _write_json(args.json, report)
    print('  edw imported from: {}'.format(edw_path))
    print('  wheel files checked: {}; RECORD entries verified: {}'.format(
        payload['wheel_files_checked'], payload['record_entries_verified']))
    print('  mandatory requirements satisfied: {}/{}'.format(
        len(requirements), len(requirements)))
    print('  visible distributions: {}'.format(len(dists)))
    return 0


def junit(args):
    import xml.etree.ElementTree as ElementTree

    root = ElementTree.parse(args.file).getroot()
    suite = root.find('testsuite') if root.tag == 'testsuites' else root
    tests = int(suite.get('tests', '0'))
    failures = int(suite.get('failures', '0'))
    errors = int(suite.get('errors', '0'))
    skipped = int(suite.get('skipped', '0'))
    report = {
        'tests': tests,
        'passed': tests - failures - errors - skipped,
        'failed': failures + errors,
        'skipped': skipped,
    }
    _write_json(args.json, report)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['failed'] == 0 and report['skipped'] == 0 else 1


def smoke_info(args):
    site = pathlib.Path(args.site)
    dists = _dist_index(site)
    payload = {
        'site': str(site.resolve()),
        'distributions': {name: dist.version for name, dist in sorted(dists.items())},
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


def _write_json(path, payload):
    if not path:
        return
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write('\n')


def main(argv=None):
    if Requirement is None:
        _fail('the `packaging` package is required for the closure check')
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)

    core = subparsers.add_parser('create-core')
    core.add_argument('--python', required=True)
    core.add_argument('--source-site', required=True)
    core.add_argument('--wheel', required=True)
    core.add_argument('--dest', required=True)
    core.add_argument('--json')
    core.set_defaults(func=create_core)

    gate = subparsers.add_parser('create-gate')
    gate.add_argument('--python', required=True)
    gate.add_argument('--source-site', required=True)
    gate.add_argument('--wheel', required=True)
    gate.add_argument('--dest', required=True)
    gate.add_argument('--json')
    gate.set_defaults(func=create_gate)

    check = subparsers.add_parser('verify')
    check.add_argument('--site', required=True)
    check.add_argument('--wheel', required=True)
    check.add_argument('--json')
    check.set_defaults(func=verify)

    report = subparsers.add_parser('junit')
    report.add_argument('--file', required=True)
    report.add_argument('--json')
    report.set_defaults(func=junit)

    info = subparsers.add_parser('smoke-info')
    info.add_argument('--site', required=True)
    info.set_defaults(func=smoke_info)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
