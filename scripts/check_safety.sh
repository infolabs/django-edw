#!/usr/bin/env bash
#
# E11/R6: fail-closed safety regression gate for django-edw.
#
# The gate never uses the network and never trusts a caller-supplied working
# directory.  It:
#
#   1. preflight: exact expected HEAD, clean tracked tree, non-optimized
#      interpreter (with a disposable -O negative probe), reviewed input and
#      test-inventory manifests, approved provider wheel bytes;
#   2. snapshot the exact commit outside the clone (`git archive`), add the
#      ignored prebuilt frontend bundle only as a pinned provenance input and
#      normalise file modes; build the wheel twice and require one digest;
#   3. inspect the wheel payload/METADATA/RECORD/provider pins;
#   4. fresh offline resolution of the mandatory closure and of the explicit
#      test/build tools, produce exact hash locks, and install them into two
#      fresh environments (mandatory-only core, runtime+tools gate);
#   5. smoke the bulk API in the mandatory-only environment;
#   6. run the product suites against the installed wheel with JUnit output,
#      read every suite with the fail-closed reader and the reviewed inventory;
#   7. verify the installed payload, provider metadata bytes and the
#      post-suite in-interpreter evidence (same interpreter, after the suite);
#   8. check migrations drift and assemble the final summary.
#
# Required environment:
#   EDW_SAFETY_EXPECTED_HEAD  exact 40-hex tested commit (not "HEAD", not unknown)
#   EDW_SAFETY_WHEELHOUSE     directory with the offline dependency wheels
#   EDW_SAFETY_PYTHON         source interpreter (build/pytest tooling)
# Optional:
#   EDW_SAFETY_WORK           base directory only; the run root is created
#                             inside it and is never deleted (compatibility)
#   EDW_SAFETY_RUN_BASE       base directory for the run root
#   EDW_SAFETY_KEEP=0         remove only the run's own disposable tmp dir
#
set -o errexit
set -o nounset
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${EDW_SAFETY_PYTHON:-python3}"
HELPER="${REPO_ROOT}/scripts/check_safety_env.py"
INPUTS="${REPO_ROOT}/scripts/safety-inputs.json"
INVENTORY="${REPO_ROOT}/scripts/safety-test-inventory.json"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore::SyntaxWarning,ignore::RuntimeWarning,ignore::ImportWarning"
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL 2>/dev/null || true
export PIP_NO_INDEX=1
export PIP_DISABLE_PIP_VERSION_CHECK=1

fail() {
    echo "SAFETY FAIL: $*" >&2
    exit 1
}

# ---------------------------------------------------------------------------
# 0. Interpreter/preconditions that must not create or delete anything yet.
# ---------------------------------------------------------------------------
if [[ ! -x "${PYTHON}" ]]; then
    # Nothing has been created: a caller-supplied EDW_SAFETY_WORK is untouched.
    fail "interpreter not found: ${PYTHON}"
fi
if [[ ! -f "${HELPER}" || ! -f "${INPUTS}" || ! -f "${INVENTORY}" ]]; then
    fail "gate inputs are missing under ${REPO_ROOT}/scripts"
fi
EXPECTED_HEAD="${EDW_SAFETY_EXPECTED_HEAD:-}"
if [[ -z "${EXPECTED_HEAD}" ]]; then
    fail "EDW_SAFETY_EXPECTED_HEAD is required (the exact tested commit)"
fi
WHEELHOUSE="${EDW_SAFETY_WHEELHOUSE:-}"
if [[ -z "${WHEELHOUSE}" || ! -d "${WHEELHOUSE}" ]]; then
    fail "EDW_SAFETY_WHEELHOUSE must name the offline wheel directory"
fi

# ---------------------------------------------------------------------------
# 1. Own disposable run root.  A caller path is only ever a *base* directory;
#    it is never deleted, and the run root gets an ownership marker.
# ---------------------------------------------------------------------------
if [[ -n "${EDW_SAFETY_WORK:-}" ]]; then
    RUN_BASE="${EDW_SAFETY_WORK}"
elif [[ -n "${EDW_SAFETY_RUN_BASE:-}" ]]; then
    RUN_BASE="${EDW_SAFETY_RUN_BASE}"
else
    RUN_BASE="${REPO_ROOT}/../.edw-safety-runs"
fi
mkdir -p "${RUN_BASE}"
RUN="$(mktemp -d "${RUN_BASE%/}/run.XXXXXXXX")"
RUN_MARKER="${RUN}/.edw-safety-run"
printf 'run=%s\npid=%s\nhead=%s\n' "${RUN}" "$$" "${EXPECTED_HEAD}" >"${RUN_MARKER}"
mkdir -p "${RUN}/tmp"
cleanup() {
    # Only the run's own disposable tmp dir may be removed; the run root (with
    # the wheel, JUnit, logs, locks and payload evidence) is kept on failure.
    if [[ "${EDW_SAFETY_KEEP:-1}" == "0" ]]; then
        rm -rf "${RUN}/tmp"
    fi
}
trap cleanup EXIT
echo "SAFETY RUN: ${RUN}"
echo "  expected HEAD: ${EXPECTED_HEAD}"

run_started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
"${PYTHON}" - "${RUN}/run.json" "${EXPECTED_HEAD}" "${PYTHON}" "${WHEELHOUSE}" "${run_started}" <<'PY'
import json
import pathlib
import sys

target, head, python, wheelhouse, started = sys.argv[1:6]
pathlib.Path(target).write_text(json.dumps({
    'schema': 'edw-modernize/safety-run/1',
    'started_at': started,
    'expected_head': head,
    'source_python': python,
    'wheelhouse': wheelhouse,
}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
PY

# ---------------------------------------------------------------------------
# 2. Preconditions (exact HEAD, clean tree, approved inputs/provider).
# ---------------------------------------------------------------------------
echo "== 1/9 preconditions =="
"${PYTHON}" "${HELPER}" preconditions \
    --repo "${REPO_ROOT}" \
    --expected-head "${EXPECTED_HEAD}" \
    --wheelhouse "${WHEELHOUSE}" \
    --inputs "${INPUTS}" \
    --inventory "${INVENTORY}" \
    --json "${RUN}/preconditions.json"

echo "== 2/9 optimized-interpreter negative probe =="
OPT_DEST="${RUN}/tmp/optimizer-probe.txt"
set +o errexit
"${PYTHON}" -O "${HELPER}" probe --dest "${OPT_DEST}" --json "${RUN}/tmp/optimizer.json" \
    >"${RUN}/optimizer-guard.log" 2>&1
OPT_RC=$?
set -o errexit
OPT_WROTE=0
[[ -e "${OPT_DEST}" ]] && OPT_WROTE=1
"${PYTHON}" - "${RUN}/optimizer-guard.json" "${OPT_RC}" "${OPT_WROTE}" <<'PY'
import json
import pathlib
import sys

target, rc, wrote = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
if rc == 0 or wrote:
    raise SystemExit(
        'SAFETY FAIL: an optimized interpreter was not refused (rc={}, wrote={})'.format(
            rc, wrote))
pathlib.Path(target).write_text(json.dumps({
    'schema': 'edw-modernize/safety/optimizer-guard/1',
    'ok': True,
    'refused_exit': rc,
    'wrote_output': bool(wrote),
}, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print('  python -O refused before any output (exit {})'.format(rc))
PY

# ---------------------------------------------------------------------------
# 3. Frozen snapshot + reproducible wheel build.
# ---------------------------------------------------------------------------
echo "== 3/9 frozen snapshot and wheel build =="
"${PYTHON}" "${HELPER}" snapshot \
    --repo "${REPO_ROOT}" \
    --expected-head "${EXPECTED_HEAD}" \
    --inputs "${INPUTS}" \
    --dest "${RUN}/src" \
    --json "${RUN}/inputs-manifest.json"
EPOCH="$("${PYTHON}" - "${INPUTS}" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1]))['source_date_epoch'])
PY
)"
echo "  source_date_epoch: ${EPOCH}"
export SOURCE_DATE_EPOCH="${EPOCH}"
mkdir -p "${RUN}/dist-a" "${RUN}/dist-b" "${RUN}/dist"
for target in dist-a dist-b; do
    "${PYTHON}" -m build --wheel --no-isolation --outdir "${RUN}/${target}" "${RUN}/src" \
        >"${RUN}/build-${target}.log" 2>&1 || {
            tail -30 "${RUN}/build-${target}.log" >&2
            fail "wheel build (${target})"
        }
done
WHEEL_A="$(ls "${RUN}/dist-a"/django_edw-*.whl)"
WHEEL_B="$(ls "${RUN}/dist-b"/django_edw-*.whl)"
SHA_A="$(sha256sum "${WHEEL_A}" | cut -d' ' -f1)"
SHA_B="$(sha256sum "${WHEEL_B}" | cut -d' ' -f1)"
[[ "${SHA_A}" == "${SHA_B}" ]] || fail "wheel build is not reproducible (${SHA_A} != ${SHA_B})"
cp "${WHEEL_A}" "${RUN}/dist/"
WHEEL="${RUN}/dist/$(basename "${WHEEL_A}")"
[[ "$(sha256sum "${WHEEL}" | cut -d' ' -f1)" == "${SHA_A}" ]] || fail "dist copy differs"
"${PYTHON}" "${HELPER}" wheel-info \
    --wheel "${WHEEL}" --inputs "${INPUTS}" --json "${RUN}/wheel.json"

# ---------------------------------------------------------------------------
# 4. Fresh offline resolution -> exact hash locks -> clean installs.
# ---------------------------------------------------------------------------
echo "== 4/9 fresh offline resolution and hash locks =="
TOOLS="$("${PYTHON}" - "${INPUTS}" <<'PY'
import json
import sys
print(' '.join(json.load(open(sys.argv[1]))['tools_roots']))
PY
)"
mkdir -p "${RUN}/locks"
"${PYTHON}" -m venv "${RUN}/resolve-env"
"${PYTHON}" "${HELPER}" resolve \
    --python "${RUN}/resolve-env/bin/python" \
    --wheel "${WHEEL}" \
    --wheelhouse "${WHEELHOUSE}" \
    --links "${RUN}/links" \
    --dist "${RUN}/dist" \
    --dest "${RUN}/locks" \
    --runtime-lock "${RUN}/locks/runtime.lock" \
    --tools-lock "${RUN}/locks/tools.lock" \
    --tools ${TOOLS} \
    --json "${RUN}/resolve.json"

echo "== 5/9 clean mandatory-only and gate environments =="
"${PYTHON}" "${HELPER}" install \
    --python "${PYTHON}" --dest "${RUN}/core-env" \
    --links "${RUN}/links" --dist "${RUN}/dist" \
    --lock "${RUN}/locks/runtime.lock" \
    --json "${RUN}/install-core.json"
"${PYTHON}" "${HELPER}" install \
    --python "${PYTHON}" --dest "${RUN}/gate-env" \
    --links "${RUN}/links" --dist "${RUN}/dist" \
    --lock "${RUN}/locks/runtime.lock" \
    --lock "${RUN}/locks/tools.lock" \
    --json "${RUN}/install-gate.json"
GATE_PY="${RUN}/gate-env/bin/python"
GATE_SITE="$("${GATE_PY}" -c 'import site; print(site.getsitepackages()[0])')"
CORE_PY="${RUN}/core-env/bin/python"
CORE_SITE="$("${CORE_PY}" -c 'import site; print(site.getsitepackages()[0])')"
export EDW_SAFETY_EVIDENCE_DIR="${RUN}/evidence"
mkdir -p "${EDW_SAFETY_EVIDENCE_DIR}"

echo "== 6/9 mandatory-only closure smoke =="
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
if site not in edw_path.parents:
    raise SystemExit('edw is not the fresh mandatory-only wheel: {}'.format(edw_path))

call_command('migrate', run_syncdb=True, verbosity=0)

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from edw.models.defaults.term import Term
from edw.tests.contract.app.models import DataMart

user = User.objects.create_superuser(
    username='safety-smoke', email='safety-smoke@example.invalid', password='not-a-secret')
client = APIClient(raise_request_exception=False)
client.force_authenticate(user=user)

response = client.post(
    '/edw/api/terms/', [{'name': 'Smoke', 'slug': 'safety-smoke-term'}], format='json')
if response.status_code not in (200, 201):
    raise SystemExit('mandatory smoke POST failed: {} {}'.format(
        response.status_code, response.content[:400]))
if not Term.objects.filter(slug='safety-smoke-term').exists():
    raise SystemExit('mandatory smoke POST did not write')

response = client.post(
    '/edw/api/terms/', [{'name': 'Smoke renamed', 'slug': 'safety-smoke-term'}],
    format='json')
if response.status_code not in (200, 201):
    raise SystemExit('mandatory smoke upsert failed: {} {}'.format(
        response.status_code, response.content[:400]))
if Term.objects.get(slug='safety-smoke-term').name != 'Smoke renamed':
    raise SystemExit('mandatory smoke upsert did not update')

response = client.delete('/edw/api/terms/?slug=missing-smoke')
if response.status_code != 400:
    raise SystemExit('unbounded collection DELETE was not refused: {}'.format(
        response.status_code))

root = Term.objects.create(name='Smoke root', slug='safety-smoke-root')
leaf = Term.objects.create(name='Smoke leaf', slug='safety-smoke-leaf', parent=root)
response = client.delete('/edw/api/terms/{}/'.format(root.pk))
if response.status_code != 400 or not Term.objects.filter(pk=leaf.pk).exists():
    raise SystemExit('detail root DELETE policy failed: {}'.format(response.status_code))

# A shared term belongs to a foreign data mart: the membership row is an
# implicit M2M-through consequence and must be refused (default-deny).
mart = DataMart.objects.create(name='Smoke mart', slug='safety-smoke-mart')
shared = Term.objects.create(name='Smoke shared', slug='safety-smoke-shared')
mart.terms.add(shared)
response = client.delete('/edw/api/terms/{}/'.format(shared.pk))
if response.status_code != 400 or not Term.objects.filter(pk=shared.pk).exists():
    raise SystemExit('shared-term M2M effect was not refused: {}'.format(
        response.status_code))

response = client.delete('/edw/api/terms/{}/'.format(leaf.pk))
if response.status_code != 204 or Term.objects.filter(pk=leaf.pk).exists():
    raise SystemExit('leaf DELETE policy failed: {}'.format(response.status_code))

print('  mandatory-only closure: setup + migrate + bulk POST/upsert + DELETE policy OK')
print('  active edw: {}'.format(edw_path))
PY

echo "== 7/9 payload evidence (pre-suite) =="
"${GATE_PY}" "${HELPER}" payload \
    --site "${GATE_SITE}" --wheel "${WHEEL}" --stage pre \
    --json "${RUN}/payload-pre.json"

# ---------------------------------------------------------------------------
# 5. Product suites against the freshly installed wheel.
# ---------------------------------------------------------------------------
run_suite() {
    local name="$1" directory="$2" settings="$3" pythonpath="$4"
    echo "== suite ${name} =="
    mkdir -p "${RUN}/junit"
    set +o errexit
    (
        cd "${REPO_ROOT}"
        PYTHONPATH="${REPO_ROOT}/${pythonpath}" DJANGO_SETTINGS_MODULE="${settings}" \
            "${GATE_PY}" -m pytest "${REPO_ROOT}/${directory}" \
            --rootdir="${REPO_ROOT}" \
            -q -p no:cacheprovider --junit-xml="${RUN}/junit/${name}.xml" \
            >"${RUN}/suite-${name}.log" 2>&1
    )
    local rc=$?
    set -o errexit
    tail -n 5 "${RUN}/suite-${name}.log" || true
    if [[ ! -f "${RUN}/junit/${name}.xml" ]]; then
        fail "suite ${name} produced no JUnit XML (exit ${rc})"
    fi
    "${PYTHON}" "${HELPER}" junit \
        --file "${RUN}/junit/${name}.xml" \
        --suite "${name}" --inventory "${INVENTORY}" \
        --json "${RUN}/junit-${name}.json" \
        || fail "suite ${name} failed the JUnit/inventory check"
    if [[ "${rc}" -ne 0 ]]; then
        fail "suite ${name} pytest exit ${rc}"
    fi
    local expected_file="${EDW_SAFETY_EVIDENCE_DIR}/post-suite-${settings}.json"
    [[ -f "${expected_file}" ]] || fail "suite ${name} wrote no post-suite evidence"
    "${PYTHON}" "${HELPER}" post-suite \
        --file "${expected_file}" --payload "${RUN}/payload-pre.json" \
        --json "${RUN}/post-suite-${name}.json" \
        || fail "suite ${name} post-suite evidence is inconsistent"
}

run_suite "runtime_tests" "runtime_tests" "edw_runtime_settings" "runtime_tests"
run_suite "runtime_tests_safety_alias" "runtime_tests_safety_alias" \
    "safety_alias_settings" "runtime_tests_safety_alias"

echo "== 8/9 payload evidence (post-suite) and migration drift =="
"${GATE_PY}" "${HELPER}" payload \
    --site "${GATE_SITE}" --wheel "${WHEEL}" --stage post \
    --json "${RUN}/payload-post.json"
set +o errexit
(
    cd "${RUN}"
    PYTHONPATH="${REPO_ROOT}/runtime_tests" DJANGO_SETTINGS_MODULE=edw_runtime_settings \
        "${GATE_PY}" -m django makemigrations --check --dry-run --verbosity=0
)
DRIFT_RC=$?
set -o errexit
[[ "${DRIFT_RC}" -eq 0 ]] || fail "unexpected migrations drift (exit ${DRIFT_RC})"
echo "  migrations drift: 0"

# ---------------------------------------------------------------------------
# 6. Final summary (any missing/inconsistent artifact is a failure).
# ---------------------------------------------------------------------------
echo "== 9/9 final summary =="
"${PYTHON}" "${HELPER}" summary \
    --run "${RUN}" \
    --suite "runtime_tests:${RUN}/junit/runtime_tests.xml:${RUN}/post-suite-runtime_tests.json" \
    --suite "runtime_tests_safety_alias:${RUN}/junit/runtime_tests_safety_alias.xml:${RUN}/post-suite-runtime_tests_safety_alias.json" \
    --json "${RUN}/summary.json"
echo "SAFETY WHEEL_SHA256=$("${PYTHON}" - "${RUN}/summary.json" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1]))['wheel_sha256'])
PY
)"
echo "SAFETY EVIDENCE=${RUN}"
echo "SAFETY PASS"
