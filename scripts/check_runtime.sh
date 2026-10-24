#!/usr/bin/env bash
#
# E7: real-runtime gate for django-edw.
#
# Unlike scripts/check.sh (historical E1-E5.fix barrier, which runs against the
# isolated E1 stubs), this gate uses only the prepared environment:
#
#   /home/agent/workspace/missions/prep/mdm-pilot/edw-bulk-integration/venv
#
# It does not import edw_contract_compat, does not put the stub directory on
# sys.path and treats a missing real package as a failure (never a skip).
#
# Steps:
#   1. preflight: exact matrix versions, four real namespaces, pip check;
#   2. copy the source tree outside the clone and build the wheel there;
#   3. install the wheel offline into the prepared environment (no index);
#   4. compare every installed edw/email_auth/social_extra file and the wheel
#      RECORD against the built wheel;
#   5. run the real-runtime tests (installed wheel, synthetic sqlite only);
#   6. check makemigrations --check --dry-run for unexpected drift.
#
# Network, pip download (no-index), npm, a live database and the historical
# mdm-pilot-real venv are not touched.  A single write database alias is used;
# no distributed atomicity is claimed by the tests.
#
set -o errexit
set -o nounset
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${EDW_RUNTIME_PYTHON:-/home/agent/workspace/missions/prep/mdm-pilot/edw-bulk-integration/venv/bin/python}"
SITE_PACKAGES="$("${PYTHON}" -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null || true)"

if [[ ! -x "${PYTHON}" ]]; then
    echo "RUNTIME FAIL: missing prepared interpreter ${PYTHON}" >&2
    exit 2
fi
if [[ -z "${SITE_PACKAGES}" || ! -d "${SITE_PACKAGES}" ]]; then
    echo "RUNTIME FAIL: cannot resolve site-packages of ${PYTHON}" >&2
    exit 2
fi

WORK="${EDW_RUNTIME_WORK:-$(mktemp -d "${REPO_ROOT}/../.edw-runtime.XXXXXX")}"
KEEP="${EDW_RUNTIME_KEEP:-0}"
cleanup() {
    if [[ "${KEEP}" != "1" ]]; then
        rm -rf "${WORK}"
    else
        echo "RUNTIME: workdir kept at ${WORK}"
    fi
}
trap cleanup EXIT

export PYTHONDONTWRITEBYTECODE=1
# Reproducible wheel digest: the same source tree produces the same archive.
# The timestamp is taken from the implementation paths only, so a later report
# or note commit does not change the wheel digest.
if [[ -z "${SOURCE_DATE_EPOCH:-}" ]]; then
    SOURCE_DATE_EPOCH="$(git -C "${REPO_ROOT}" log -1 --format=%ct -- \
        backend pyproject.toml runtime_tests scripts 2>/dev/null || echo 0)"
fi
export SOURCE_DATE_EPOCH
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export DJANGO_SETTINGS_MODULE=edw_runtime_settings
export PYTHONPATH="${REPO_ROOT}/runtime_tests"

echo "== 1/6 preflight: real matrix and namespaces =="
"${PYTHON}" - <<'PY'
import importlib
import importlib.util
import pathlib
import sys
from importlib import metadata

MATRIX = {
    'Django': '5.2.18',
    'djangorestframework': '3.18.3',
    'django-bitfield': '2.4.0',
    'djangorestframework-bulk': '0.3.0a1',
    'django-filter': '26.2',
    'djangorestframework-filters': '1.0.0.dev2',
    'djangorestframework-recursive': '0.1.2',
}
NAMESPACES = {
    'bitfield': 'django-bitfield',
    'rest_framework_bulk': 'djangorestframework-bulk',
    'rest_framework_filters': 'djangorestframework-filters',
    'rest_framework_recursive': 'djangorestframework-recursive',
}

for distribution, expected in MATRIX.items():
    installed = metadata.version(distribution)
    assert installed == expected, '{} {} != {}'.format(distribution, installed, expected)
    print('  {}=={}'.format(distribution, installed))

for module_name, distribution in NAMESPACES.items():
    module = importlib.import_module(module_name)
    path = pathlib.Path(module.__file__).resolve()
    assert '/stubs/' not in path.as_posix(), '{} from stub: {}'.format(module_name, path)
    dist_path = pathlib.Path(metadata.distribution(distribution).locate_file(
        module_name + '/__init__.py')).resolve()
    assert path == dist_path, '{} is not provided by {}: {}'.format(module_name, distribution, path)
    print('  {} <- {}'.format(module_name, distribution))

assert importlib.util.find_spec('edw_contract_compat') is None, (
    'edw_contract_compat must not be importable in the real runtime'
)
stub_suffix = '/edw/tests/contract/stubs'
assert not [entry for entry in sys.path if str(entry).replace('\\', '/').endswith(stub_suffix)]
print('  no edw_contract_compat, no stub path')
PY

echo "== pip check (prepared environment) =="
"${PYTHON}" -m pip check

echo "== 2/6 build wheel outside the clone =="
mkdir -p "${WORK}/src" "${WORK}/dist"
tar -C "${REPO_ROOT}" \
    --exclude=.git \
    --exclude=build \
    --exclude='*.egg-info' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='frontend/node_modules' \
    --exclude='docs/_build' \
    --exclude='.edw-runtime*' \
    --exclude='*.sqlite3' \
    --exclude='*.dshclaim' \
    -cf - . | tar -C "${WORK}/src" -xf -

"${PYTHON}" -m build --wheel --no-isolation --outdir "${WORK}/dist" "${WORK}/src" \
    >"${WORK}/build.log" 2>&1 || { cat "${WORK}/build.log" >&2; echo "RUNTIME FAIL: wheel build" >&2; exit 1; }

WHEEL="$(ls "${WORK}"/dist/django_edw-*.whl)"
WHEEL_SHA="$(sha256sum "${WHEEL}" | cut -d' ' -f1)"
echo "  wheel: $(basename "${WHEEL}")"
echo "  wheel sha256: ${WHEEL_SHA}"

echo "== 3/6 install wheel into the prepared environment (offline) =="
verify_install() {
    "${PYTHON}" - "${WHEEL}" "${SITE_PACKAGES}" <<'PY'
import base64
import csv
import glob
import hashlib
import pathlib
import sys
import zipfile

wheel_path = pathlib.Path(sys.argv[1])
site_packages = pathlib.Path(sys.argv[2])
top_levels = {'edw', 'email_auth', 'social_extra'}
mismatches = []
compared = 0

with zipfile.ZipFile(wheel_path) as wheel:
    names = wheel.namelist()
    for name in names:
        if name.endswith('/'):
            continue
        if name.split('/', 1)[0] not in top_levels:
            continue
        installed = site_packages / name
        if not installed.is_file():
            mismatches.append('missing: {}'.format(name))
            continue
        expected = hashlib.sha256(wheel.read(name)).hexdigest()
        actual = hashlib.sha256(installed.read_bytes()).hexdigest()
        if expected != actual:
            mismatches.append('differs: {}'.format(name))
        compared += 1

record_paths = glob.glob(str(site_packages / 'django_edw-*.dist-info' / 'RECORD'))
assert record_paths, 'django-edw RECORD not found after install'
record_path = pathlib.Path(record_paths[0])
record_entries = 0
with record_path.open(newline='', encoding='utf-8') as handle:
    for row in csv.reader(handle):
        if not row:
            continue
        name, hash_field = row[0], row[1] if len(row) > 1 else ''
        if not hash_field:
            continue
        algorithm, value = hash_field.split('=', 1)
        assert algorithm == 'sha256', algorithm
        target = site_packages / name
        if not target.is_file():
            mismatches.append('record missing: {}'.format(name))
            continue
        actual = base64.urlsafe_b64encode(
            hashlib.sha256(target.read_bytes()).digest()
        ).rstrip(b'=').decode('ascii')
        if actual != value:
            mismatches.append('record hash: {}'.format(name))
        record_entries += 1

import edw
edw_path = pathlib.Path(edw.__file__).resolve()
assert 'site-packages' in edw_path.parts, 'edw is not the installed package: {}'.format(edw_path)
assert (site_packages / 'edw' / 'rest' / 'serializers' / 'bulk.py').is_file(), (
    'installed wheel lost the bulk admission module'
)

print('  active edw: {}'.format(edw_path))
print('  compared source files: {}'.format(compared))
print('  RECORD entries verified: {}'.format(record_entries))
print('  mismatches: {}'.format(len(mismatches)))
for item in mismatches[:20]:
    print('    {}'.format(item))
if mismatches:
    raise SystemExit(1)
PY
}

if verify_install >"${WORK}/install-compare-before.log" 2>&1; then
    echo "  prepared environment already matches the built wheel; install skipped"
    cat "${WORK}/install-compare-before.log"
else
    "${PYTHON}" -m pip install --no-index --no-deps --force-reinstall --no-compile "${WHEEL}" \
        >"${WORK}/install.log" 2>&1 || {
            cat "${WORK}/install.log" >&2
            echo "RUNTIME FAIL: install into the prepared environment" >&2
            exit 1
        }
    tail -n 2 "${WORK}/install.log"
fi

echo "== 4/6 compare installed sources and RECORD =="
verify_install

echo "== pip check (installed metadata) =="
"${PYTHON}" -m pip check

echo "== 5/6 real-runtime tests (installed wheel, synthetic sqlite) =="
set +o errexit
(
    cd "${WORK}"
    "${PYTHON}" -m pytest "${REPO_ROOT}/runtime_tests" \
        -q -p no:cacheprovider --junit-xml="${WORK}/junit.xml"
)
PYTEST_STATUS=$?
set -o errexit

if [[ -f "${WORK}/junit.xml" ]]; then
    "${PYTHON}" - "${WORK}/junit.xml" <<'PY'
import sys
import xml.etree.ElementTree as ElementTree

root = ElementTree.parse(sys.argv[1]).getroot()
suite = root.find('testsuite') if root.tag == 'testsuites' else root
tests = int(suite.get('tests', '0'))
failures = int(suite.get('failures', '0'))
errors = int(suite.get('errors', '0'))
skipped = int(suite.get('skipped', '0'))
print('TESTS passed={} failed={} errors={} skipped={}'.format(
    tests - failures - errors - skipped, failures, errors, skipped))
raise SystemExit(0 if failures + errors == 0 else 1)
PY
    TESTS_STATUS=$?
else
    echo "RUNTIME FAIL: pytest produced no junit report" >&2
    TESTS_STATUS=1
fi
if [[ ${PYTEST_STATUS} -ne 0 || ${TESTS_STATUS} -ne 0 ]]; then
    echo "RUNTIME FAIL: runtime tests (pytest exit ${PYTEST_STATUS})" >&2
    exit 1
fi

echo "== 6/6 migrations drift =="
set +o errexit
(
    cd "${WORK}"
    "${PYTHON}" -m django makemigrations --check --dry-run --verbosity=0
)
DRIFT_STATUS=$?
set -o errexit
if [[ ${DRIFT_STATUS} -ne 0 ]]; then
    echo "RUNTIME FAIL: unexpected migrations drift (makemigrations --check exit ${DRIFT_STATUS})" >&2
    exit 1
fi
echo "MIGRATIONS_DRIFT=0"

echo "STUB_MODULES_ACTIVE=0"
echo "RUNTIME WHEEL_SHA256=${WHEEL_SHA}"
echo "RUNTIME PASS"
