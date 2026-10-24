#!/usr/bin/env bash
#
# E9/R6: safety regression gate for django-edw.
#
# This is the durable product gate for the bounded R1-R6 safety repair.  It
# never runs pip/npm install and never touches the network:
#
#   1. preflight: exact matrix versions, real namespaces (no E1 stubs), no
#      edw_contract_compat, `pip check` of the prepared environment;
#   2. build the wheel twice outside the clone from a copy of the tree and
#      require a reproducible digest;
#   3. verify the wheel payload (packages, RECORD hashes, no legacy code);
#   4. materialise a *fresh mandatory-only closure* environment (only the
#      wheel's mandatory Requires-Dist closure plus the wheel) and a fresh gate
#      environment (same wheel + declared test/build tooling), without any
#      installer;
#   5. smoke the repaired bulk API in the mandatory-only environment;
#   6. run the product regression suites against the freshly built wheel:
#        runtime_tests (E7 contracts + E9 R1-R4 negatives)
#        runtime_tests_safety_alias (E9 R5 write-alias / read-replica)
#      Zero failures, zero errors and zero skips are required;
#   7. check migrations drift;
#   8. print the evidence counters used by edw-safety-report.json.
#
# Required interpreter: any offline environment with the accepted matrix plus
# `build`, `pytest` and `pytest-django`.  Override with EDW_SAFETY_PYTHON.
#
set -o errexit
set -o nounset
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${EDW_SAFETY_PYTHON:-python3}"
KEEP="${EDW_SAFETY_KEEP:-0}"
WORK="${EDW_SAFETY_WORK:-$(mktemp -d "${REPO_ROOT}/../.edw-safety.XXXXXX")}"

cleanup() {
    if [[ "${KEEP}" != "1" ]]; then
        rm -rf "${WORK}"
    else
        echo "SAFETY: workdir kept at ${WORK}"
    fi
}
trap cleanup EXIT

export PYTHONDONTWRITEBYTECODE=1
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore::SyntaxWarning,ignore::RuntimeWarning,ignore::ImportWarning"

if [[ ! -x "${PYTHON}" ]]; then
    echo "SAFETY FAIL: interpreter not found: ${PYTHON}" >&2
    exit 2
fi

SOURCE_SITE="$("${PYTHON}" -c 'import site; print(site.getsitepackages()[0])' 2>/dev/null || true)"
if [[ -z "${SOURCE_SITE}" || ! -d "${SOURCE_SITE}" ]]; then
    echo "SAFETY FAIL: cannot resolve site-packages of ${PYTHON}" >&2
    exit 2
fi

if [[ -z "${SOURCE_DATE_EPOCH:-}" ]]; then
    SOURCE_DATE_EPOCH="$(git -C "${REPO_ROOT}" log -1 --format=%ct -- \
        backend pyproject.toml runtime_tests runtime_tests_safety_alias scripts 2>/dev/null || echo 1792847103)"
fi
export SOURCE_DATE_EPOCH

echo "== 1/8 preflight: matrix, real namespaces, no stubs =="
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
print('  python: {}'.format(sys.version.split()[0]))
for distribution, expected in MATRIX.items():
    installed = metadata.version(distribution)
    assert installed == expected, '{} {} != {}'.format(distribution, installed, expected)
    print('  {}=={}'.format(distribution, installed))
for module_name, distribution in NAMESPACES.items():
    module = importlib.import_module(module_name)
    path = pathlib.Path(module.__file__).resolve()
    assert '/stubs/' not in path.as_posix(), '{} imported from stubs: {}'.format(module_name, path)
    dist_path = pathlib.Path(metadata.distribution(distribution).locate_file(
        module_name + '/__init__.py')).resolve()
    assert path == dist_path, '{} is not provided by {}: {}'.format(
        module_name, distribution, path)
    print('  {} <- {}'.format(module_name, distribution))
assert importlib.util.find_spec('edw_contract_compat') is None, (
    'edw_contract_compat must not be importable in the real runtime')
assert not [entry for entry in sys.path
            if str(entry).replace('\\', '/').endswith('/edw/tests/contract/stubs')]
print('  no edw_contract_compat, no stub path')
PY
"${PYTHON}" -m pip check

echo "== 2/8 wheel: build outside the clone twice (reproducible) =="
mkdir -p "${WORK}/src" "${WORK}/dist-a" "${WORK}/dist-b"
tar -C "${REPO_ROOT}" \
    --exclude=.git --exclude=build --exclude='*.egg-info' --exclude=__pycache__ \
    --exclude=.pytest_cache --exclude=frontend/node_modules --exclude=docs/_build \
    --exclude='*.sqlite3' --exclude='*.dshclaim' \
    -cf - . | tar -C "${WORK}/src" -xf -
for target in dist-a dist-b; do
    "${PYTHON}" -m build --wheel --no-isolation --outdir "${WORK}/${target}" "${WORK}/src" \
        >"${WORK}/build-${target}.log" 2>&1 || {
            tail -20 "${WORK}/build-${target}.log" >&2
            echo "SAFETY FAIL: wheel build (${target})" >&2
            exit 2
        }
done
WHEEL_A="$(ls "${WORK}/dist-a"/django_edw-*.whl)"
WHEEL_B="$(ls "${WORK}/dist-b"/django_edw-*.whl)"
WHEEL_SHA_A="$(sha256sum "${WHEEL_A}" | cut -d' ' -f1)"
WHEEL_SHA_B="$(sha256sum "${WHEEL_B}" | cut -d' ' -f1)"
if [[ "${WHEEL_SHA_A}" != "${WHEEL_SHA_B}" ]]; then
    echo "SAFETY FAIL: wheel build is not reproducible (${WHEEL_SHA_A} != ${WHEEL_SHA_B})" >&2
    exit 2
fi
WHEEL="${WHEEL_A}"
WHEEL_SHA="${WHEEL_SHA_A}"
WHEEL_NAME="$(basename "${WHEEL}")"
echo "  wheel: ${WHEEL_NAME}"
echo "  wheel sha256: ${WHEEL_SHA}"
echo "  source_date_epoch: ${SOURCE_DATE_EPOCH}"
echo "  repo HEAD: $(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"

echo "== 3/8 fresh gate environment (wheel + declared tooling, no install) =="
"${PYTHON}" "${REPO_ROOT}/scripts/check_safety_env.py" create-gate \
    --python "${PYTHON}" \
    --source-site "${SOURCE_SITE}" \
    --wheel "${WHEEL}" \
    --dest "${WORK}/gate-env" \
    --json "${WORK}/gate-env.json"
GATE_PY="${WORK}/gate-env/bin/python"
GATE_SITE="$("${GATE_PY}" -c 'import site; print(site.getsitepackages()[0])')"
PYTHONPATH="${GATE_SITE}" "${PYTHON}" "${REPO_ROOT}/scripts/check_safety_env.py" verify \
    --site "${GATE_SITE}" --wheel "${WHEEL}" --json "${WORK}/verify-gate.json"

echo "== 4/8 fresh mandatory-only closure environment (no install) =="
"${PYTHON}" "${REPO_ROOT}/scripts/check_safety_env.py" create-core \
    --python "${PYTHON}" \
    --source-site "${SOURCE_SITE}" \
    --wheel "${WHEEL}" \
    --dest "${WORK}/core-env" \
    --json "${WORK}/core-env.json"
CORE_PY="${WORK}/core-env/bin/python"
CORE_SITE="$("${CORE_PY}" -c 'import site; print(site.getsitepackages()[0])')"
PYTHONPATH="${CORE_SITE}" "${PYTHON}" "${REPO_ROOT}/scripts/check_safety_env.py" verify \
    --site "${CORE_SITE}" --wheel "${WHEEL}" --json "${WORK}/verify-core.json"
CORE_CLOSURE="$("${PYTHON}" -c "import json,sys; print(len(json.load(open(sys.argv[1]))['required_distributions']))" "${WORK}/core-env.json")"
echo "  mandatory runtime closure size: ${CORE_CLOSURE} distributions"

echo "== 5/8 mandatory-only closure smoke (bulk API on the new wheel) =="
PYTHONPATH="${REPO_ROOT}/runtime_tests" CORE_SITE="${CORE_SITE}" \
DJANGO_SETTINGS_MODULE=edw_runtime_settings \
"${CORE_PY}" - <<'PY'
import os
import pathlib

import django

django.setup()
import edw
from django.core.management import call_command

site = pathlib.Path(os.environ['CORE_SITE']).resolve()
edw_path = pathlib.Path(edw.__file__).resolve()
assert site in edw_path.parents, 'edw is not the fresh mandatory-only wheel: {}'.format(edw_path)

call_command('migrate', run_syncdb=True, verbosity=0)

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from edw.models.defaults.term import Term

user = User.objects.create_superuser(
    username='safety-smoke', email='safety-smoke@example.invalid', password='not-a-secret')
client = APIClient()
client.force_authenticate(user=user)

response = client.post(
    '/edw/api/terms/', [{'name': 'Smoke', 'slug': 'safety-smoke-term'}], format='json')
assert response.status_code in (200, 201), response.content[:500]
assert Term.objects.filter(slug='safety-smoke-term').exists()

response = client.post(
    '/edw/api/terms/', [{'name': 'Smoke renamed', 'slug': 'safety-smoke-term'}], format='json')
assert response.status_code in (200, 201), response.content[:500]
assert Term.objects.get(slug='safety-smoke-term').name == 'Smoke renamed'

response = client.delete('/edw/api/terms/?slug=missing-smoke')
assert response.status_code == 400, response.content[:500]
assert Term.objects.filter(slug='safety-smoke-term').exists()

root = Term.objects.create(name='Smoke root', slug='safety-smoke-root')
leaf = Term.objects.create(name='Smoke leaf', slug='safety-smoke-leaf', parent=root)
response = client.delete('/edw/api/terms/{}/'.format(root.pk))
assert response.status_code == 400, response.content[:500]
assert Term.objects.filter(pk=root.pk).exists() and Term.objects.filter(pk=leaf.pk).exists()

response = client.delete('/edw/api/terms/{}/'.format(leaf.pk))
assert response.status_code == 204, response.content[:500]
assert not Term.objects.filter(pk=leaf.pk).exists()

print('  mandatory-only closure: django.setup + migrate + bulk POST/upsert + DELETE policy OK')
print('  active edw: {}'.format(edw_path))
PY
"${CORE_PY}" -m pip check 2>/dev/null || echo "  note: pip is not part of the mandatory closure (expected)"

echo "== 6/8 product regression suites against the new wheel =="
mkdir -p "${WORK}/junit"
set +o errexit
PYTHONPATH="${REPO_ROOT}/runtime_tests" DJANGO_SETTINGS_MODULE=edw_runtime_settings \
"${GATE_PY}" -m pytest "${REPO_ROOT}/runtime_tests" \
    -q -p no:cacheprovider --junit-xml="${WORK}/junit/runtime.xml" \
    >"${WORK}/runtime-tests.log" 2>&1
RUNTIME_RC=$?
PYTHONPATH="${REPO_ROOT}/runtime_tests_safety_alias" DJANGO_SETTINGS_MODULE=safety_alias_settings \
"${GATE_PY}" -m pytest "${REPO_ROOT}/runtime_tests_safety_alias" \
    -q -p no:cacheprovider --junit-xml="${WORK}/junit/alias.xml" \
    >"${WORK}/alias-tests.log" 2>&1
ALIAS_RC=$?
set -o errexit
tail -n 3 "${WORK}/runtime-tests.log"
tail -n 3 "${WORK}/alias-tests.log"
if [[ -f "${WORK}/junit/runtime.xml" ]]; then
    "${PYTHON}" "${REPO_ROOT}/scripts/check_safety_env.py" junit \
        --file "${WORK}/junit/runtime.xml" --json "${WORK}/junit-runtime.json" || true
fi
if [[ -f "${WORK}/junit/alias.xml" ]]; then
    "${PYTHON}" "${REPO_ROOT}/scripts/check_safety_env.py" junit \
        --file "${WORK}/junit/alias.xml" --json "${WORK}/junit-alias.json" || true
fi
if [[ "${RUNTIME_RC}" -ne 0 || "${ALIAS_RC}" -ne 0 ]]; then
    echo "SAFETY FAIL: regression suites (runtime=${RUNTIME_RC}, alias=${ALIAS_RC})" >&2
    exit 1
fi

echo "== 7/8 migrations drift =="
set +o errexit
(
    cd "${WORK}"
    PYTHONPATH="${REPO_ROOT}/runtime_tests" DJANGO_SETTINGS_MODULE=edw_runtime_settings \
    "${GATE_PY}" -m django makemigrations --check --dry-run --verbosity=0
)
DRIFT_RC=$?
set -o errexit
if [[ "${DRIFT_RC}" -ne 0 ]]; then
    echo "SAFETY FAIL: unexpected migrations drift (exit ${DRIFT_RC})" >&2
    exit 1
fi
echo "  migrations drift: 0"

echo "== 8/8 evidence counters =="
"${PYTHON}" - "${WORK}" "${WHEEL_NAME}" "${WHEEL_SHA}" "${CORE_CLOSURE}" <<'PY'
import json
import pathlib
import sys

work, wheel_name, wheel_sha, closure = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
counts = {}
for label in ('runtime', 'alias'):
    path = pathlib.Path(work, 'junit-{}.json'.format(label))
    if not path.is_file():
        raise SystemExit('SAFETY FAIL: missing junit counts for {}'.format(label))
    counts[label] = json.loads(path.read_text())
report = {
    'wheel': wheel_name,
    'wheel_sha256': wheel_sha,
    'mandatory_closure': closure,
    'runtime_suite': counts['runtime'],
    'alias_suite': counts['alias'],
    'tests_passed': counts['runtime']['passed'] + counts['alias']['passed'],
    'tests_failed': counts['runtime']['failed'] + counts['alias']['failed'],
    'tests_skipped': counts['runtime']['skipped'] + counts['alias']['skipped'],
    'migrations_drift': 0,
}
pathlib.Path(work, 'safety-summary.json').write_text(
    json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2, sort_keys=True))
if report['tests_failed'] or report['tests_skipped']:
    raise SystemExit('SAFETY FAIL: failures={} skips={}'.format(
        report['tests_failed'], report['tests_skipped']))
PY

echo "SAFETY WHEEL_SHA256=${WHEEL_SHA}"
echo "SAFETY PASS"
