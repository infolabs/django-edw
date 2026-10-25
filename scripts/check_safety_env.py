#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E9/E11-R6: offline, fail-closed helpers for the EDW safety regression gate.

The gate never uses the network and never trusts a caller-supplied working
directory.  It builds the wheel from the *exact* expected commit snapshot,
resolves and installs the mandatory closure into fresh environments with exact
hash locks, runs the product suites against that wheel and verifies the
installed payload in the same test interpreter after the whole suite.

Every check below is written with explicit ``if`` failures (no ``assert``), and
the module refuses to run under an optimized interpreter before it writes any
output, so ``python -O`` cannot turn a trust check into a no-op.

Subcommands::

    preconditions   exact HEAD, clean tracked tree, non-optimized interpreter,
                    reviewed inputs/inventory, approved provider bytes
    snapshot        frozen source tree from the exact commit + pinned ignored
                    frontend bundle, normalized modes
    wheel-info      wheel metadata/payload/RECORD/frontend bundle/provider pins
    resolve         fresh offline resolution -> exact hash locks (runtime/tools)
    install         clean venv install from a hash lock; closure/RECORD/pip check
    payload         installed payload/RECORD/provider/METADATA check (pre/post)
    post-suite      verify post-suite in-interpreter evidence (same interpreter)
    junit           fail-closed all-suite JUnit reader with exact inventory
    probe           tiny side-effect used by the -O guard (must refuse under -O)
    summary         assemble the final run summary, fail on any missing evidence
"""
from __future__ import unicode_literals

import argparse
import base64
import csv
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ElementTree
import zipfile

try:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
except ImportError:  # pragma: no cover - the tool environment provides packaging
    Requirement = None

SCHEMA_PREFIX = 'edw-modernize/safety'
PRODUCT_DISTRIBUTION = 'django-edw'
PRODUCT_VERSION = '0.2.0'
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
ADMINISTRATIVE_DISTRIBUTIONS = ('pip', 'setuptools', 'wheel')


def _fail(message, code=2):
    sys.stderr.write('SAFETY FAIL: {}\n'.format(message))
    raise SystemExit(code)


def _require_not_optimized(stage):
    if sys.flags.optimize:
        _fail('optimized Python (-O, optimize={}) is refused before {}'.format(
            sys.flags.optimize, stage))
    if not __debug__:
        _fail('Python was started with assertions disabled; trust checks are refused')


def _write_json(path, payload):
    if not path:
        return
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.tmp')
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n',
                         encoding='utf-8')
    os.replace(str(temporary), str(target))


def _read_json(path, label):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
    except Exception as exc:
        _fail('cannot read {} {}: {!r}'.format(label, path, exc))


def _sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _run(command, label, cwd=None, env=None):
    result = subprocess.run(
        command, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        _fail('{} failed (exit {}):\n{}'.format(
            label, result.returncode, (result.stdout or '')[-4000:]))
    return result.stdout or ''


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def _load_inputs(path):
    inputs = _read_json(path, 'safety inputs')
    if inputs.get('schema') != SCHEMA_PREFIX + '-inputs/1':
        _fail('unexpected safety inputs schema: {!r}'.format(inputs.get('schema')))
    epoch = inputs.get('source_date_epoch')
    if not isinstance(epoch, int) or epoch <= 0:
        _fail('source_date_epoch must be a positive integer')
    bundle = inputs.get('frontend_bundle') or {}
    if bundle.get('path') and len(str(bundle.get('sha256', ''))) != 64:
        _fail('frontend bundle sha256 must be a 64-hex digest')
    provider = inputs.get('expected_provider') or {}
    if provider.get('distribution') != 'djangorestframework-bulk':
        _fail('the approved provider distribution is not djangorestframework-bulk')
    if len(str(provider.get('wheel_sha256', ''))) != 64:
        _fail('the approved provider wheel sha256 is missing')
    matrix = inputs.get('matrix')
    if not isinstance(matrix, dict) or not matrix:
        _fail('matrix is missing from safety inputs')
    tools = inputs.get('tools_roots')
    if not isinstance(tools, list) or not tools:
        _fail('tools_roots is missing from safety inputs')
    return inputs


def _load_inventory(path):
    inventory = _read_json(path, 'test inventory')
    if inventory.get('schema') != SCHEMA_PREFIX + '-test-inventory/1':
        _fail('unexpected test inventory schema: {!r}'.format(inventory.get('schema')))
    suites = inventory.get('suites')
    if not isinstance(suites, dict) or not suites:
        _fail('test inventory has no suites')
    seen = set()
    for name, suite in suites.items():
        cases = suite.get('cases')
        if not isinstance(cases, list) or not cases:
            _fail('suite {} has no reviewed cases'.format(name))
        for case in cases:
            if not isinstance(case, str) or '::' not in case:
                _fail('suite {} has a malformed case id {!r}'.format(name, case))
            if case in seen:
                _fail('duplicate case id in the inventory: {}'.format(case))
            seen.add(case)
    return inventory


# --------------------------------------------------------------------------- #
# preconditions
# --------------------------------------------------------------------------- #
def preconditions(args):
    _require_not_optimized('any output write')
    expected = str(args.expected_head or '')
    if len(expected) != 40 or any(ch not in '0123456789abcdef' for ch in expected):
        _fail('--expected-head must be the exact 40-hex tested commit')
    repo = pathlib.Path(args.repo).resolve()
    if not (repo / '.git').exists():
        _fail('not a git checkout: {}'.format(repo))
    head = _run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], 'git rev-parse').strip()
    if head != expected:
        _fail('HEAD {} is not the expected tested commit {}'.format(head, expected))
    status = _run(['git', '-C', str(repo), 'status', '--porcelain=v1',
                   '--untracked-files=no'], 'git status')
    if status.strip():
        _fail('the tracked worktree is not clean:\n{}'.format(status[:2000]))
    inputs = _load_inputs(args.inputs)
    inventory = _load_inventory(args.inventory)
    wheelhouse = pathlib.Path(args.wheelhouse).resolve()
    if not wheelhouse.is_dir():
        _fail('wheelhouse is not a directory: {}'.format(wheelhouse))
    wheels = sorted(wheelhouse.glob('*.whl'))
    if not wheels:
        _fail('wheelhouse has no wheels: {}'.format(wheelhouse))
    provider = inputs['expected_provider']
    provider_wheel_hash = None
    for wheel in wheels:
        if canonicalize_name(wheel.name.split('-')[0]) == canonicalize_name(
                provider['distribution']):
            provider_wheel_hash = _sha256_file(wheel)
    if provider_wheel_hash != provider['wheel_sha256']:
        _fail('approved provider wheel hash mismatch: {} != {}'.format(
            provider_wheel_hash, provider['wheel_sha256']))
    bundle = inputs.get('frontend_bundle') or {}
    if bundle.get('path'):
        bundle_path = repo / bundle['path']
        if not bundle_path.is_file():
            _fail('pinned frontend bundle input is missing: {}'.format(bundle['path']))
        if _sha256_file(bundle_path) != bundle['sha256']:
            _fail('frontend bundle bytes do not match the pinned provenance input')
    report = {
        'schema': SCHEMA_PREFIX + '-preconditions/1',
        'ok': True,
        'head': head,
        'expected_head': expected,
        'python': sys.version.split()[0],
        'optimize': int(sys.flags.optimize),
        'repo': str(repo),
        'wheelhouse': str(wheelhouse),
        'wheelhouse_wheels': len(wheels),
        'wheelhouse_sha256': {
            wheel.name: _sha256_file(wheel) for wheel in wheels
        },
        'tracked_tree_clean': True,
        'inputs_sha256': _sha256_file(args.inputs),
        'inventory_sha256': _sha256_file(args.inventory),
        'inventory_suites': {
            name: len(suite['cases']) for name, suite in inventory['suites'].items()
        },
        'source_date_epoch': inputs['source_date_epoch'],
        'provider_wheel_sha256': provider_wheel_hash,
        'matrix': inputs['matrix'],
    }
    _write_json(args.json, report)
    print('  preconditions: HEAD {} clean tracked tree'.format(head[:12]))
    print('  wheelhouse: {} wheels; approved provider {}'.format(
        len(wheels), str(provider_wheel_hash)[:12]))
    print('  reviewed suites: {}'.format(
        ', '.join('{}={}'.format(k, v) for k, v in report['inventory_suites'].items())))
    return 0


# --------------------------------------------------------------------------- #
# snapshot
# --------------------------------------------------------------------------- #
def snapshot(args):
    _require_not_optimized('the frozen snapshot write')
    expected = str(args.expected_head)
    repo = pathlib.Path(args.repo).resolve()
    inputs = _load_inputs(args.inputs)
    dest = pathlib.Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest.parent / 'source.tar'
    with archive.open('wb') as handle:
        result = subprocess.run(
            ['git', '-C', str(repo), 'archive', '--format=tar', expected],
            stdout=handle, stderr=subprocess.PIPE,
        )
    if result.returncode != 0:
        _fail('git archive failed: {}'.format(result.stderr.decode('utf-8', 'replace')))
    archive_sha = _sha256_file(archive)
    with tarfile.open(str(archive), 'r:') as tar:
        for member in tar.getmembers():
            member.mode = 0o755 if member.isdir() else 0o644
        tar.extractall(str(dest), filter='data')
    archive.unlink()
    bundle = inputs.get('frontend_bundle') or {}
    bundle_sha = None
    if bundle.get('path'):
        source = repo / bundle['path']
        target = dest / bundle['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        bundle_sha = _sha256_file(target)
        if bundle_sha != bundle['sha256']:
            _fail('the ignored frontend bundle does not match its pinned hash')
    for path in sorted(dest.rglob('*')):
        if path.is_dir():
            path.chmod(0o755)
        else:
            path.chmod(0o644)
    tree = _run(['git', '-C', str(repo), 'rev-parse', expected + '^{tree}'],
                'git rev-parse tree').strip()
    listed = _run(['git', '-C', str(repo), 'ls-tree', '-r', '--full-tree', expected],
                  'git ls-tree')
    (dest.parent / 'git-tree.txt').write_text(listed, encoding='utf-8')
    files = sorted(
        str(path.relative_to(dest)) for path in dest.rglob('*') if path.is_file())
    manifest = {
        'schema': SCHEMA_PREFIX + '-inputs-manifest/1',
        'ok': True,
        'head': expected,
        'tree': tree,
        'archive_sha256': archive_sha,
        'git_tree_listing_sha256': _sha256_bytes(listed.encode('utf-8')),
        'frontend_bundle_path': bundle.get('path'),
        'frontend_bundle_sha256': bundle_sha,
        'source_date_epoch': inputs['source_date_epoch'],
        'file_modes': 'files 0644, directories 0755',
        'file_count': len(files),
    }
    _write_json(args.json, manifest)
    print('  snapshot: {} files from {} (tree {})'.format(
        len(files), expected[:12], tree[:12]))
    print('  pinned frontend bundle: {}'.format(bundle_sha))
    return 0


# --------------------------------------------------------------------------- #
# wheel-info
# --------------------------------------------------------------------------- #
def _wheel_metadata_text(wheel):
    with zipfile.ZipFile(str(wheel)) as archive:
        names = [name for name in archive.namelist()
                 if name.endswith('.dist-info/METADATA')]
        if len(names) != 1:
            _fail('expected exactly one METADATA in the wheel, found {}'.format(names))
        return archive.read(names[0]).decode('utf-8')


def _mandatory_requirements(metadata_text):
    requirements = []
    for line in metadata_text.splitlines():
        if not line.startswith('Requires-Dist:'):
            continue
        requirement = Requirement(line.split(':', 1)[1].strip())
        if requirement.marker is not None:
            try:
                if not requirement.marker.evaluate({'extra': ''}):
                    continue
            except Exception:
                continue
        requirements.append(requirement)
    return requirements


def wheel_info(args):
    _require_not_optimized('the wheel inspection')
    wheel = pathlib.Path(args.wheel).resolve()
    inputs = _load_inputs(args.inputs)
    if not wheel.is_file():
        _fail('wheel is missing: {}'.format(wheel))
    with zipfile.ZipFile(str(wheel)) as archive:
        names = archive.namelist()
        metadata_text = _wheel_metadata_text(wheel)
        fields = {}
        for line in metadata_text.splitlines():
            if ':' not in line:
                continue
            key, value = line.split(':', 1)
            fields.setdefault(key.strip(), value.strip())
        if canonicalize_name(fields.get('Name', '')) != canonicalize_name(
                PRODUCT_DISTRIBUTION):
            _fail('unexpected wheel name: {!r}'.format(fields.get('Name')))
        if fields.get('Version') != PRODUCT_VERSION:
            _fail('unexpected wheel version: {!r}'.format(fields.get('Version')))
        required = {'edw/__init__.py', 'email_auth/__init__.py',
                    'social_extra/__init__.py'}
        missing = sorted(required - set(names))
        if missing:
            _fail('wheel does not export packages: {}'.format(missing))
        legacy = [name for name in names
                  if name.startswith('backend/') or name.startswith('sandbox/')
                  or '/sandbox/' in name]
        if legacy:
            _fail('legacy code leaked into the wheel: {}'.format(legacy[:5]))
        probe_migrations = [
            name for name in names
            if name.startswith('edw/tests/contract/app/migrations/0002_')
        ]
        if len(probe_migrations) != 1:
            _fail('wheel is missing the E11 synthetic probe migration: {}'.format(
                probe_migrations))
        bundle = inputs.get('frontend_bundle') or {}
        bundle_sha = None
        if bundle.get('path'):
            member = 'edw/static/edw/js/bundle.js'
            if member not in names:
                _fail('wheel is missing the prebuilt frontend bundle {}'.format(member))
            bundle_sha = _sha256_bytes(archive.read(member))
            if bundle_sha != bundle['sha256']:
                _fail('wheel frontend bundle does not match the pinned provenance input')
        record_names = [name for name in names if name.endswith('.dist-info/RECORD')]
        if len(record_names) != 1:
            _fail('expected exactly one RECORD, found {}'.format(record_names))
        record_rows = 0
        for row in archive.read(record_names[0]).decode('utf-8').splitlines():
            if not row:
                continue
            parts = row.split(',')
            if len(parts) < 2 or not parts[1]:
                continue
            algorithm = parts[1].split('=', 1)[0]
            if algorithm != 'sha256':
                _fail('unexpected RECORD hash algorithm {}'.format(algorithm))
            record_rows += 1
    requirements = [
        {'requirement': str(requirement), 'name': canonicalize_name(requirement.name)}
        for requirement in _mandatory_requirements(metadata_text)
    ]
    report = {
        'schema': SCHEMA_PREFIX + '-wheel/1',
        'ok': True,
        'wheel': str(wheel),
        'name': fields.get('Name'),
        'version': fields.get('Version'),
        'sha256': _sha256_file(wheel),
        'size_bytes': wheel.stat().st_size,
        'payload_files': len(names),
        'record_entries': record_rows,
        'metadata_sha256': _sha256_bytes(metadata_text.encode('utf-8')),
        'frontend_bundle_sha256': bundle_sha,
        'mandatory_requirements': requirements,
    }
    _write_json(args.json, report)
    print('  wheel: {} {} bytes={} sha256={}'.format(
        report['name'], report['version'], report['size_bytes'], report['sha256']))
    print('  payload files: {}; RECORD entries: {}; frontend bundle: {}'.format(
        report['payload_files'], report['record_entries'], bundle_sha))
    return 0


# --------------------------------------------------------------------------- #
# resolve
# --------------------------------------------------------------------------- #
def _prepare_links(wheelhouse, links):
    _require_not_optimized('the offline link preparation')
    wheelhouse = pathlib.Path(wheelhouse).resolve()
    links = pathlib.Path(links).resolve()
    links.mkdir(parents=True, exist_ok=True)
    copied = {}
    for wheel in sorted(wheelhouse.glob('*.whl')):
        if canonicalize_name(wheel.name.split('-')[0]) == canonicalize_name(
                PRODUCT_DISTRIBUTION):
            continue  # the candidate is built from the exact snapshot
        target = links / wheel.name
        target.write_bytes(wheel.read_bytes())
        copied[wheel.name] = _sha256_file(target)
    if not copied:
        _fail('the wheelhouse has no dependency wheels')
    return copied


def _pip_report(python, links, dist, report_path, requirements, constraints=None):
    command = [
        python, '-m', 'pip', 'install', '--dry-run', '--report', str(report_path),
        '--no-index', '--find-links', str(links), '--find-links', str(dist),
        '--ignore-installed', '--no-cache-dir', '--disable-pip-version-check',
        '--no-compile',
    ]
    if constraints:
        command += ['-c', str(constraints)]
    command += list(requirements)
    return _run(command, 'offline resolution')


def _report_entries(report_path):
    report = _read_json(report_path, 'pip resolution report')
    entries = []
    for item in report.get('install', []):
        metadata = item.get('metadata') or {}
        download = item.get('download_info') or {}
        archive = download.get('archive_info') or {}
        hashes = archive.get('hashes') or {}
        digest = hashes.get('sha256')
        if not digest:
            raw = archive.get('hash') or ''
            for separator in ('=', ':'):
                if raw.startswith('sha256' + separator):
                    digest = raw.split(separator, 1)[1]
                    break
        if not digest or len(digest) != 64:
            _fail('pip report entry has no sha256 hash: {}'.format(metadata.get('name')))
        entries.append({
            'name': canonicalize_name(metadata.get('name', '')),
            'version': metadata.get('version'),
            'sha256': digest,
            'url': download.get('url'),
        })
    if not entries:
        _fail('offline resolution produced no distributions')
    return entries


def _entry_wheel_name(entry):
    return (entry.get('url') or '').rsplit('/', 1)[-1]


def _write_lock(path, pins):
    path = pathlib.Path(path)
    lines = ['# E11 fresh offline resolution; exact hashes; no network.']
    for name, (version, digest) in sorted(pins.items()):
        lines.append('{}=={} --hash=sha256:{}'.format(name, version, digest))
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def resolve(args):
    _require_not_optimized('the resolution lock write')
    wheel = pathlib.Path(args.wheel).resolve()
    wheel_sha = _sha256_file(wheel)
    links = pathlib.Path(args.links)
    copied = _prepare_links(args.wheelhouse, links)
    dist = pathlib.Path(args.dist).resolve()
    if not (dist / wheel.name).is_file():
        _fail('the candidate wheel was not copied into the dist directory')
    if _sha256_file(dist / wheel.name) != wheel_sha:
        _fail('the dist copy of the candidate wheel differs from the built wheel')
    dest = pathlib.Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    runtime_report = dest / 'runtime-resolve.json'
    _pip_report(args.python, links, dist, runtime_report,
                ['django-edw=={}'.format(PRODUCT_VERSION)])
    runtime_entries = _report_entries(runtime_report)
    runtime_pins = {}
    for entry in runtime_entries:
        if entry['name'] == canonicalize_name(PRODUCT_DISTRIBUTION):
            expected = wheel_sha
        else:
            name = _entry_wheel_name(entry)
            if name not in copied:
                _fail('resolved distribution {} is not in the prepared links'.format(
                    entry['name']))
            expected = copied[name]
        if entry['sha256'] != expected:
            _fail('resolution hash mismatch for {}'.format(entry['name']))
        runtime_pins[entry['name']] = (entry['version'], entry['sha256'])
    if canonicalize_name(PRODUCT_DISTRIBUTION) not in runtime_pins:
        _fail('the candidate distribution is missing from the runtime resolution')

    constraints = dest / 'runtime-constraints.txt'
    constraints.write_text(''.join(
        '{}=={}\n'.format(name, version)
        for name, (version, _hash) in sorted(runtime_pins.items())
    ), encoding='utf-8')
    tools_report = dest / 'tools-resolve.json'
    _pip_report(args.python, links, dist, tools_report, list(args.tools),
                constraints=constraints)
    tool_entries = _report_entries(tools_report)
    tools_pins = {}
    for entry in tool_entries:
        if entry['name'] in runtime_pins:
            if runtime_pins[entry['name']][0] != entry['version']:
                _fail('a tool requires a different {} version ({}) than the runtime '
                      'lock'.format(entry['name'], entry['version']))
            continue
        name = _entry_wheel_name(entry)
        if name not in copied:
            _fail('resolved tool {} is not in the prepared links'.format(entry['name']))
        if copied[name] != entry['sha256']:
            _fail('resolved tool wheel does not match the copied hash: {}'.format(
                entry['name']))
        tools_pins[entry['name']] = (entry['version'], entry['sha256'])
    if not tools_pins:
        _fail('the tools resolution is empty')

    runtime_lock = pathlib.Path(args.runtime_lock)
    tools_lock = pathlib.Path(args.tools_lock)
    _write_lock(runtime_lock, runtime_pins)
    _write_lock(tools_lock, tools_pins)
    report = {
        'schema': SCHEMA_PREFIX + '-resolve/1',
        'ok': True,
        'runtime_lock': str(runtime_lock),
        'runtime_lock_sha256': _sha256_file(runtime_lock),
        'runtime_distributions': {
            name: version for name, (version, _h) in sorted(runtime_pins.items())},
        'tools_lock': str(tools_lock),
        'tools_lock_sha256': _sha256_file(tools_lock),
        'tools_distributions': {
            name: version for name, (version, _h) in sorted(tools_pins.items())},
        'links': copied,
    }
    _write_json(args.json, report)
    print('  resolved runtime closure: {} distributions'.format(len(runtime_pins)))
    print('  resolved explicit tools: {} distributions'.format(len(tools_pins)))
    return 0


# --------------------------------------------------------------------------- #
# install
# --------------------------------------------------------------------------- #
def _venv_python(venv):
    return str(pathlib.Path(venv) / 'bin' / 'python')


def _site_packages(venv):
    python = _venv_python(venv)
    return pathlib.Path(_run(
        [python, '-c', 'import site; print(site.getsitepackages()[0])'],
        'venv site-packages').strip())


def _distributions(site_dir):
    import importlib.metadata as metadata
    result = {}
    for dist in metadata.distributions(path=[str(site_dir)]):
        name = dist.metadata['Name']
        if name:
            result[canonicalize_name(name)] = dist.version
    return result


def _record_check(site_dir):
    site_dir = pathlib.Path(site_dir)
    entries = 0
    checked = 0
    missing = []
    mismatches = []
    for dist_info in sorted(site_dir.glob('django_edw-*.dist-info')):
        record = dist_info / 'RECORD'
        if not record.is_file():
            missing.append(str(record))
            continue
        with record.open(newline='', encoding='utf-8') as handle:
            for row in csv.reader(handle):
                if not row or len(row) < 2 or not row[1]:
                    continue
                name, hash_field = row[0], row[1]
                entries += 1
                algorithm, expected = hash_field.split('=', 1)
                target = site_dir / name
                if not target.is_file():
                    missing.append(name)
                    continue
                actual = base64.urlsafe_b64encode(
                    hashlib.sha256(target.read_bytes()).digest()).rstrip(b'=').decode()
                checked += 1
                if algorithm != 'sha256' or actual != expected:
                    mismatches.append(name)
    return entries, checked, mismatches, missing


def install(args):
    _require_not_optimized('the environment creation')
    venv = pathlib.Path(args.dest).resolve()
    if venv.exists():
        _fail('refusing to reuse an existing environment: {}'.format(venv))
    _run([args.python, '-m', 'venv', str(venv)], 'venv creation')
    python = _venv_python(venv)
    pip_version = _run([python, '-m', 'pip', '--version'], 'pip version').strip()
    locks = [pathlib.Path(item) for item in args.lock]
    for lock in locks:
        if not lock.is_file():
            _fail('lock file is missing: {}'.format(lock))
    command = [python, '-m', 'pip', 'install', '--no-index',
               '--find-links', str(args.links), '--find-links', str(args.dist),
               '--require-hashes', '--no-cache-dir', '--no-compile',
               '--disable-pip-version-check', '--no-input']
    for lock in locks:
        command += ['-r', str(lock)]
    _run(command, 'hash-locked offline install')
    check = _run([python, '-m', 'pip', 'check'], 'pip check').strip()
    site_dir = _site_packages(venv)
    installed = _distributions(site_dir)
    edw_file = pathlib.Path(_run(
        [python, '-c', 'import edw; print(edw.__file__)'],
        'venv edw origin').strip()).resolve()
    if site_dir.resolve() not in edw_file.parents:
        _fail('edw is not imported from the fresh environment: {}'.format(edw_file))
    record_entries, record_checked, mismatches, missing = _record_check(site_dir)
    if mismatches or missing:
        _fail('installed RECORD does not match the environment: {} / {}'.format(
            mismatches[:5], missing[:5]))
    expected = set()
    for lock in locks:
        for line in lock.read_text(encoding='utf-8').splitlines():
            if line and not line.startswith('#'):
                expected.add(canonicalize_name(line.split('==', 1)[0]))
    unexpected = sorted(set(installed) - expected - set(ADMINISTRATIVE_DISTRIBUTIONS))
    if unexpected:
        _fail('unexpected distributions in the fresh environment: {}'.format(unexpected))
    missing_locked = sorted(expected - set(installed))
    if missing_locked:
        _fail('locked distributions are missing from the environment: {}'.format(
            missing_locked))
    report = {
        'schema': SCHEMA_PREFIX + '-install/1',
        'ok': True,
        'venv': str(venv),
        'python': _run([python, '-c', 'import sys; print(sys.version.split()[0])'],
                       'venv python version').strip(),
        'administrative_pip': pip_version,
        'administrative_distributions': {
            name: installed[name] for name in ADMINISTRATIVE_DISTRIBUTIONS
            if name in installed
        },
        'locks': [{'path': str(lock), 'sha256': _sha256_file(lock)} for lock in locks],
        'distributions': installed,
        'edw_file': str(edw_file),
        'record_entries': record_entries,
        'record_checked': record_checked,
        'pip_check': check,
    }
    _write_json(args.json, report)
    print('  fresh environment: {} distributions ({} locked + administrative)'.format(
        len(installed), len(expected)))
    print('  edw imported from: {}'.format(edw_file))
    print('  RECORD entries verified: {}/{}'.format(record_checked, record_entries))
    print('  pip check: {}'.format(check))
    return 0


# --------------------------------------------------------------------------- #
# payload (pre/post installed evidence)
# --------------------------------------------------------------------------- #
def payload(args):
    _require_not_optimized('the installed payload evidence')
    site_dir = pathlib.Path(args.site).resolve()
    wheel = pathlib.Path(args.wheel).resolve()
    if not site_dir.is_dir():
        _fail('site-packages is missing: {}'.format(site_dir))
    with zipfile.ZipFile(str(wheel)) as archive:
        names = archive.namelist()
        payload_checked = 0
        for name in names:
            if name.endswith('/'):
                continue
            if name.endswith('.dist-info/RECORD'):
                # pip regenerates RECORD at install time; its integrity is
                # verified by the record check below, not by byte equality.
                continue
            target = site_dir / name
            if not target.is_file():
                _fail('installed wheel file is missing: {}'.format(name))
            if _sha256_bytes(archive.read(name)) != _sha256_bytes(target.read_bytes()):
                _fail('installed wheel file differs from the wheel payload: {}'.format(name))
            payload_checked += 1
        wheel_payload_files = len([name for name in names if not name.endswith('/')])
    record_entries, record_checked, mismatches, missing = _record_check(site_dir)
    if mismatches or missing:
        _fail('RECORD check failed: mismatches={} missing={}'.format(
            mismatches[:5], missing[:5]))
    import edw
    edw_file = pathlib.Path(edw.__file__).resolve()
    if site_dir not in edw_file.parents:
        _fail('edw is imported from outside the environment: {}'.format(edw_file))
    metadata_text = _wheel_metadata_text(wheel)
    report = {
        'schema': SCHEMA_PREFIX + '-payload/1',
        'ok': True,
        'stage': args.stage,
        'site': str(site_dir),
        'wheel_sha256': _sha256_file(wheel),
        'metadata_sha256': _sha256_bytes(metadata_text.encode('utf-8')),
        'payload_files_checked': payload_checked,
        'wheel_payload_files': wheel_payload_files,
        'record_entries': record_entries,
        'record_checked': record_checked,
        'edw_file': str(edw_file),
        'python': _run([sys.executable, '-c',
                        'import sys; print(sys.version.split()[0])'],
                       'interpreter version').strip(),
        'providers': {},
    }
    import importlib.metadata as metadata
    for module_name, distribution in PROVIDER_DISTRIBUTIONS.items():
        dist = metadata.distribution(distribution)
        module = __import__(module_name)
        module_file = pathlib.Path(module.__file__).resolve()
        if site_dir not in module_file.parents:
            _fail('provider {} is imported outside the environment: {}'.format(
                module_name, module_file))
        candidates = sorted(site_dir.glob('{}*.dist-info'.format(
            distribution.replace('-', '_'))))
        if len(candidates) != 1:
            _fail('ambiguous provider metadata for {}: {}'.format(
                distribution, [str(path) for path in candidates]))
        entry = {
            'distribution': distribution,
            'version': dist.version,
            'module_file': str(module_file),
            'module_sha256': _sha256_file(module_file),
            'metadata_sha256': _sha256_file(candidates[0] / 'METADATA'),
            'record_sha256': _sha256_file(candidates[0] / 'RECORD'),
        }
        report['providers'][module_name] = entry
    _write_json(args.json, report)
    print('  payload[{}]: {} files, {} RECORD entries, providers ok'.format(
        args.stage, payload_checked, record_checked))
    return 0


# --------------------------------------------------------------------------- #
# post-suite
# --------------------------------------------------------------------------- #
def post_suite(args):
    _require_not_optimized('the post-suite evidence check')
    payload_pre = _read_json(args.payload, 'pre-suite payload report')
    site_dir = pathlib.Path(payload_pre['site']).resolve()
    evidence = _read_json(args.file, 'post-suite evidence')
    if 'error' in evidence:
        _fail('the post-suite interpreter evidence failed: {}'.format(evidence['error']))
    checks = {
        'exitstatus': (evidence.get('exitstatus'), 0),
        'optimize': (evidence.get('optimize'), 0),
        'edw_contract_compat_importable': (
            evidence.get('edw_contract_compat_importable'), False),
        'active_stub_modules': (evidence.get('active_stub_modules'), []),
        'stub_sys_path_entries': (evidence.get('stub_sys_path_entries'), []),
        'edw_modules_outside_site': (evidence.get('edw_modules_outside_site'), []),
        'record_mismatch': (evidence.get('record_mismatch'), []),
        'record_missing': (evidence.get('record_missing'), []),
    }
    for name, (actual, expected) in checks.items():
        if actual != expected:
            _fail('post-suite {} is {!r}, expected {!r}'.format(name, actual, expected))
    if evidence.get('site') != str(site_dir):
        _fail('post-suite evidence was recorded in another site: {} != {}'.format(
            evidence.get('site'), site_dir))
    edw_file = pathlib.Path(str(evidence.get('edw_file'))).resolve()
    if site_dir not in edw_file.parents:
        _fail('post-suite edw origin is outside the gate environment: {}'.format(edw_file))
    if evidence.get('dist_version') != PRODUCT_VERSION:
        _fail('post-suite django-edw version is {!r}'.format(evidence.get('dist_version')))
    if evidence.get('record_entries') != payload_pre['record_entries']:
        _fail('post-suite RECORD entry count changed: {!r} != {!r}'.format(
            evidence.get('record_entries'), payload_pre['record_entries']))
    if evidence.get('record_checked') != evidence.get('record_entries'):
        _fail('post-suite RECORD was not fully verified')
    for module_name in REAL_NAMESPACES:
        namespace = (evidence.get('namespaces') or {}).get(module_name)
        if not namespace or not namespace.get('file'):
            _fail('post-suite namespace {} was not imported'.format(module_name))
        if site_dir not in pathlib.Path(namespace['file']).resolve().parents:
            _fail('post-suite namespace {} comes from outside the environment: {}'.format(
                module_name, namespace['file']))
        provider = (evidence.get('providers') or {}).get(module_name) or {}
        provider_pre = payload_pre['providers'].get(module_name) or {}
        if provider.get('version') != provider_pre.get('version'):
            _fail('provider {} version changed after the suite'.format(module_name))
        if provider.get('record_sha256') != provider_pre.get('record_sha256'):
            _fail('provider {} metadata bytes changed after the suite'.format(module_name))
        if provider.get('module_sha256') != provider_pre.get('module_sha256'):
            _fail('provider {} module bytes changed after the suite'.format(module_name))
    report = {
        'schema': SCHEMA_PREFIX + '-post-suite/1',
        'ok': True,
        'file': str(pathlib.Path(args.file).resolve()),
        'file_sha256': _sha256_file(args.file),
        'site': str(site_dir),
        'settings': evidence.get('settings'),
        'record_entries': evidence.get('record_entries'),
        'exitstatus': evidence.get('exitstatus'),
    }
    _write_json(args.json, report)
    print('  post-suite[{}]: same interpreter, {} RECORD entries, real namespaces'.format(
        evidence.get('settings'), evidence.get('record_entries')))
    return 0


# --------------------------------------------------------------------------- #
# junit
# --------------------------------------------------------------------------- #
def junit(args):
    """Fail-closed all-suite JUnit reader.  Never uses ``assert``."""
    _require_not_optimized('the JUnit read')
    path = pathlib.Path(args.file)
    if not path.is_file():
        _fail('JUnit file is missing: {}'.format(path), code=3)
    try:
        root = ElementTree.parse(str(path)).getroot()
    except Exception as exc:
        _fail('malformed JUnit XML: {!r}'.format(exc), code=3)
    if root.tag == 'testsuite':
        suites = [root]
    elif root.tag == 'testsuites':
        suites = root.findall('testsuite')
        if not suites:
            _fail('JUnit report has no testsuite', code=3)
    else:
        _fail('unexpected JUnit root {!r}'.format(root.tag), code=3)
    counters = {'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
    cases = []
    problems = []
    for index, suite in enumerate(suites):
        declared = {}
        for name in counters:
            raw = suite.get(name, '0')
            try:
                value = int(raw)
            except (TypeError, ValueError):
                _fail('testsuite[{}] has a malformed {}={!r}'.format(index, name, raw),
                      code=3)
            if value < 0:
                _fail('testsuite[{}] has a negative {}={}'.format(index, name, value),
                      code=3)
            declared[name] = value
            counters[name] += value
        testcases = suite.findall('testcase')
        if declared['tests'] != len(testcases):
            problems.append(
                'testsuite[{}] declares {} tests but contains {} testcase nodes'.format(
                    index, declared['tests'], len(testcases)))
        for case in testcases:
            classname = case.get('classname') or ''
            name = case.get('name') or ''
            if not classname or not name:
                problems.append('testcase without classname/name in suite {}'.format(index))
                continue
            case_id = '{}::{}'.format(classname, name)
            if (case.find('failure') is not None or case.find('error') is not None
                    or case.find('skipped') is not None):
                problems.append('failing/erroring/skipped testcase: {}'.format(case_id))
            cases.append(case_id)
        if declared['failures'] != len(suite.findall('testcase/failure')):
            problems.append('testsuite[{}] failure counter disagrees with nodes'.format(index))
        if declared['errors'] != len(suite.findall('testcase/error')):
            problems.append('testsuite[{}] error counter disagrees with nodes'.format(index))
    duplicates = sorted({case for case in cases if cases.count(case) > 1})
    if duplicates:
        problems.append('duplicate testcase ids: {}'.format(duplicates[:5]))
    if counters['tests'] == 0:
        problems.append('zero collected/executed tests')
    if counters['failures'] or counters['errors'] or counters['skipped']:
        problems.append('non-zero counters: {}'.format(counters))
    inventory_result = None
    if args.inventory:
        inventory = _load_inventory(args.inventory)
        suite_name = args.suite
        if suite_name is None:
            _fail('--inventory requires --suite', code=3)
        if suite_name not in inventory['suites']:
            _fail('suite {!r} is not in the reviewed inventory'.format(suite_name), code=3)
        expected = set(inventory['suites'][suite_name]['cases'])
        actual = set(cases)
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        inventory_result = {
            'suite': suite_name,
            'expected': len(expected),
            'actual': len(actual),
            'missing': missing,
            'unknown': unknown,
        }
        if missing:
            problems.append('reviewed cases did not run: {}'.format(missing[:10]))
        if unknown:
            problems.append('unreviewed cases ran: {}'.format(unknown[:10]))
    report = {
        'schema': SCHEMA_PREFIX + '-junit/1',
        'ok': not problems,
        'file': str(path.resolve()),
        'file_sha256': _sha256_file(path),
        'suites': len(suites),
        'tests': counters['tests'],
        'passed': counters['tests'] - counters['failures'] - counters['errors']
                  - counters['skipped'],
        'failed': counters['failures'] + counters['errors'],
        'errors': counters['errors'],
        'skipped': counters['skipped'],
        'cases': sorted(cases),
        'inventory': inventory_result,
        'problems': problems,
    }
    _write_json(args.json, report)
    if problems:
        for problem in problems:
            sys.stderr.write('SAFETY FAIL: JUnit: {}\n'.format(problem))
        return 1
    print(json.dumps({key: report[key] for key in
                      ('tests', 'passed', 'failed', 'errors', 'skipped')},
                     sort_keys=True))
    return 0


# --------------------------------------------------------------------------- #
# optimizer guard / probe
# --------------------------------------------------------------------------- #
def probe(args):
    _require_not_optimized('the probe write')
    target = pathlib.Path(args.dest)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('probe\n', encoding='utf-8')
    _write_json(args.json, {'schema': SCHEMA_PREFIX + '-probe/1', 'ok': True})
    return 0


# --------------------------------------------------------------------------- #
# summary
# --------------------------------------------------------------------------- #
def summary(args):
    _require_not_optimized('the final summary')
    run = pathlib.Path(args.run).resolve()
    required = {
        'preconditions': run / 'preconditions.json',
        'snapshot': run / 'inputs-manifest.json',
        'wheel': run / 'wheel.json',
        'resolve': run / 'resolve.json',
        'core_install': run / 'install-core.json',
        'gate_install': run / 'install-gate.json',
        'payload_pre': run / 'payload-pre.json',
        'payload_post': run / 'payload-post.json',
    }
    data = {}
    for key, path in required.items():
        if not path.is_file():
            _fail('required run artifact is missing: {}'.format(path))
        data[key] = _read_json(path, key)
        if data[key].get('ok') is not True:
            _fail('run artifact {} is not ok'.format(path))
    suites = {}
    for suite in args.suite:
        name, junit_path, post_path = suite.split(':', 2)
        junit_report = _read_json(run / 'junit-{}.json'.format(name), 'junit ' + name)
        post_report = _read_json(run / 'post-suite-{}.json'.format(name),
                                 'post-suite ' + name)
        if junit_report.get('ok') is not True:
            _fail('suite {} did not pass the JUnit check'.format(name))
        if post_report.get('ok') is not True:
            _fail('suite {} has no consistent post-suite evidence'.format(name))
        suites[name] = {
            'tests': junit_report['tests'],
            'passed': junit_report['passed'],
            'failed': junit_report['failed'],
            'junit': junit_path,
            'post_suite': post_path,
        }
    tests = sum(item['tests'] for item in suites.values())
    passed = sum(item['passed'] for item in suites.values())
    failed = sum(item['failed'] for item in suites.values())
    if failed:
        _fail('failed tests in the final summary')
    report = {
        'schema': SCHEMA_PREFIX + '-summary/1',
        'ok': True,
        'run': str(run),
        'head': data['preconditions']['head'],
        'tree': data['snapshot']['tree'],
        'wheel': data['wheel']['wheel'],
        'wheel_sha256': data['wheel']['sha256'],
        'frontend_bundle_sha256': data['wheel']['frontend_bundle_sha256'],
        'provider_wheel_sha256': data['preconditions']['provider_wheel_sha256'],
        'source_date_epoch': data['snapshot']['source_date_epoch'],
        'mandatory_closure': len(data['resolve']['runtime_distributions']),
        'tools': len(data['resolve']['tools_distributions']),
        'runtime_lock_sha256': data['resolve']['runtime_lock_sha256'],
        'tools_lock_sha256': data['resolve']['tools_lock_sha256'],
        'core_edw_file': data['core_install']['edw_file'],
        'gate_edw_file': data['gate_install']['edw_file'],
        'record_entries': data['payload_post']['record_entries'],
        'payload_files': data['payload_post']['payload_files_checked'],
        'suites': suites,
        'tests': tests,
        'tests_passed': passed,
        'tests_failed': failed,
    }
    _write_json(args.json, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv=None):
    if Requirement is None:
        _fail('the packaging package is required for the closure checks')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    item = sub.add_parser('preconditions')
    item.add_argument('--repo', required=True)
    item.add_argument('--expected-head', required=True)
    item.add_argument('--wheelhouse', required=True)
    item.add_argument('--inputs', required=True)
    item.add_argument('--inventory', required=True)
    item.add_argument('--json')
    item.set_defaults(func=preconditions)

    item = sub.add_parser('snapshot')
    item.add_argument('--repo', required=True)
    item.add_argument('--expected-head', required=True)
    item.add_argument('--inputs', required=True)
    item.add_argument('--dest', required=True)
    item.add_argument('--json')
    item.set_defaults(func=snapshot)

    item = sub.add_parser('wheel-info')
    item.add_argument('--wheel', required=True)
    item.add_argument('--inputs', required=True)
    item.add_argument('--json')
    item.set_defaults(func=wheel_info)

    item = sub.add_parser('resolve')
    item.add_argument('--python', required=True)
    item.add_argument('--wheel', required=True)
    item.add_argument('--wheelhouse', required=True)
    item.add_argument('--links', required=True)
    item.add_argument('--dist', required=True)
    item.add_argument('--dest', required=True)
    item.add_argument('--runtime-lock', required=True)
    item.add_argument('--tools-lock', required=True)
    item.add_argument('--tools', nargs='+', required=True)
    item.add_argument('--json')
    item.set_defaults(func=resolve)

    item = sub.add_parser('install')
    item.add_argument('--python', required=True)
    item.add_argument('--dest', required=True)
    item.add_argument('--links', required=True)
    item.add_argument('--dist', required=True)
    item.add_argument('--lock', action='append', required=True)
    item.add_argument('--json')
    item.set_defaults(func=install)

    item = sub.add_parser('payload')
    item.add_argument('--site', required=True)
    item.add_argument('--wheel', required=True)
    item.add_argument('--stage', choices=('pre', 'post'), required=True)
    item.add_argument('--json')
    item.set_defaults(func=payload)

    item = sub.add_parser('post-suite')
    item.add_argument('--file', required=True)
    item.add_argument('--payload', required=True)
    item.add_argument('--json')
    item.set_defaults(func=post_suite)

    item = sub.add_parser('junit')
    item.add_argument('--file', required=True)
    item.add_argument('--json')
    item.add_argument('--suite')
    item.add_argument('--inventory')
    item.set_defaults(func=junit)

    item = sub.add_parser('probe')
    item.add_argument('--dest', required=True)
    item.add_argument('--json')
    item.set_defaults(func=probe)

    item = sub.add_parser('summary')
    item.add_argument('--run', required=True)
    item.add_argument('--suite', action='append', default=[])
    item.add_argument('--json')
    item.set_defaults(func=summary)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
