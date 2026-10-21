#!/usr/bin/env bash
#
# E1/E2/E4: характеризационная проверка контрактов django-edw, упаковки,
# матрицы зависимостей, миграций и прав API.
#
# 1. сверяет pyproject.toml с целевой матрицей G0.1 из edw-inventory.json;
# 2. собирает wheel из pyproject.toml (PEP 517, --no-isolation, без сети)
#    и проверяет, что wheel и editable-сборка экспортируют пакеты edw,
#    email_auth, social_extra, а не backend.edw, и не тянут sandbox;
# 3. прогоняет миграции: makemigrations --check --dry-run (drift),
#    накат на пустую sqlite и накат через --fake-initial на синтетический
#    снимок прежней схемы (таблицы без миграций);
# 4. проверяет адаптеры зависимостей на офлайн-стеке матрицы;
# 5. прогоняет контрактные тесты E1/E3, права API E4 (edw.rest.permissions,
#    DataMartPermission) и тесты матрицы, импортируя edw из собранного wheel.
#
# pip/npm install не вызываются, внешние БД и сеть не используются:
# только sqlite (в памяти и файловая) и локальный locmem-кэш.
#
set -o errexit
set -o nounset
set -o pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="/home/agent/workspace/venvs/edw-modernize/bin/python"
BACKEND="${REPO_ROOT}/backend"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/edw-check.XXXXXX")"

cleanup() {
    rm -rf "${WORK}"
    rm -rf "${REPO_ROOT}/build"
    rm -rf "${REPO_ROOT}/backend/"*.egg-info
    rm -rf "${REPO_ROOT}/"*.egg-info
}
trap cleanup EXIT

if [[ ! -x "${PYTHON}" ]]; then
    echo "CHECK FAIL: не найден offline-python ${PYTHON}" >&2
    exit 2
fi

export PYTHONDONTWRITEBYTECODE=1
export PYTHONWARNINGS="ignore::DeprecationWarning,ignore::SyntaxWarning,ignore::RuntimeWarning,ignore::ImportWarning"

cd "${REPO_ROOT}"

echo "== EDW contracts check =="
"${PYTHON}" -c "import django, rest_framework, pytest; print('python: {}'.format(__import__('sys').version.split()[0])); print('django: {}'.format(django.get_version())); print('drf: {}'.format(rest_framework.VERSION)); print('pytest: {}'.format(pytest.__version__))"

echo "== 1/5 матрица зависимостей G0.1 =="
if ! PYTHONPATH="${BACKEND}" DJANGO_SETTINGS_MODULE="edw_contract_settings" \
        "${PYTHON}" -c 'from edw.tests.contract import matrix; raise SystemExit(matrix.main())'; then
    echo "CHECK FAIL: pyproject.toml расходится с матрицей G0.1" >&2
    exit 1
fi

echo "== 2/5 сборка wheel (PEP 517) =="
if ! "${PYTHON}" -m build --wheel --no-isolation --outdir "${WORK}/dist" "${REPO_ROOT}" >"${WORK}/build.log" 2>&1; then
    cat "${WORK}/build.log" >&2
    echo "CHECK FAIL: wheel не собрался" >&2
    exit 1
fi
WHEEL="$(ls "${WORK}"/dist/*.whl)"
echo "wheel: $(basename "${WHEEL}")"

"${PYTHON}" - "${WHEEL}" <<'PY'
import sys
import zipfile

wheel = sys.argv[1]
names = zipfile.ZipFile(wheel).namelist()

required = {'edw/__init__.py', 'email_auth/__init__.py', 'social_extra/__init__.py'}
missing = sorted(required - set(names))
assert not missing, 'wheel не экспортирует пакеты: {}'.format(missing)

legacy = [
    name for name in names
    if name.startswith('backend/') or name.startswith('sandbox/') or '/sandbox/' in name
]
assert not legacy, 'в wheel попал legacy-код: {}'.format(legacy[:5])

# E4: миграции синтетического контура должны попадать в wheel вместе с тестами.
assert 'edw/tests/contract/app/migrations/0001_initial.py' in names, (
    'wheel потерял миграции контрактного приложения'
)

templates = sum(1 for name in names if name.startswith('edw/templates/'))
static = sum(1 for name in names if name.startswith('edw/static/'))
locale = sum(1 for name in names if name.startswith('edw/locale/'))
assert templates and static and locale, 'wheel потерял package data'

print('  пакеты: edw, email_auth, social_extra')
print('  package data: templates={}, static={}, locale={}'.format(templates, static, locale))
PY

echo "== 2/5 проверка editable =="
if ! "${PYTHON}" - "${WORK}/editable" "${BACKEND}" >"${WORK}/editable.log" 2>&1 <<'PY'; then
import os
import sys
import zipfile

from setuptools import build_meta

out, backend = sys.argv[1], os.path.realpath(sys.argv[2])
wheel = build_meta.build_editable(out)
if not os.path.isabs(wheel):
    wheel = os.path.join(out, wheel)
archive = zipfile.ZipFile(wheel)
names = archive.namelist()

top_level = [name for name in names if name.endswith('top_level.txt')]
assert top_level, 'editable wheel без top_level.txt'
tops = archive.read(top_level[0]).decode().split()
assert 'edw' in tops, 'editable не экспортирует edw: {}'.format(tops)
assert 'backend' not in tops, 'editable экспортирует backend вместо edw: {}'.format(tops)

mapped = False
for name in names:
    if name.endswith('.pth'):
        for line in archive.read(name).decode().splitlines():
            line = line.strip()
            if line and not line.startswith('import') and os.path.realpath(line) == backend:
                mapped = True
if not mapped:
    for name in names:
        if 'finder' in name:
            code = archive.read(name).decode()
            if "'edw'" in code and 'backend.edw' not in code:
                mapped = True
assert mapped, 'editable не отображает edw на backend/edw'

print('  editable: top-level {}'.format(' '.join(tops)))
PY
    cat "${WORK}/editable.log" >&2
    echo "CHECK FAIL: editable-сборка не прошла проверку" >&2
    exit 1
fi
grep '^  editable:' "${WORK}/editable.log" || true

echo "== 3/5 миграции (drift, пустая sqlite, снимок прежней схемы) =="
MIGRATION_DB="${WORK}/migrations"
mkdir -p "${MIGRATION_DB}"

run_migration() {
    local mode="$1" db="$2" log="$3"
    rm -f "${db}"
    if ! EDW_CONTRACT_DB="${db}" PYTHONPATH="${BACKEND}" DJANGO_SETTINGS_MODULE="edw_contract_settings" \
            "${PYTHON}" "${REPO_ROOT}/scripts/check_migrations.py" "${mode}" >"${log}" 2>&1; then
        cat "${log}" >&2
        echo "CHECK FAIL: миграции (${mode})" >&2
        return 1
    fi
    grep -E '^(MIGRATION OK|  ORM|  таблиц)' "${log}" || true
    grep '^SCHEMA:' "${log}" | sed 's/^SCHEMA://' >"${log}.schema.json" || true
    return 0
}

run_migration drift "${MIGRATION_DB}/drift.sqlite3" "${MIGRATION_DB}/drift.log"
run_migration apply "${MIGRATION_DB}/empty.sqlite3" "${MIGRATION_DB}/apply.log"

# Прежняя схема: таблицы созданы без миграций (как у старой инсталляции).
run_migration legacy "${MIGRATION_DB}/legacy.sqlite3" "${MIGRATION_DB}/legacy.log"
# Накат миграций на этот же снимок: --fake-initial не должен пересоздавать таблицы.
if ! EDW_CONTRACT_DB="${MIGRATION_DB}/legacy.sqlite3" PYTHONPATH="${BACKEND}" \
        DJANGO_SETTINGS_MODULE="edw_contract_settings" \
        "${PYTHON}" "${REPO_ROOT}/scripts/check_migrations.py" fake \
        >"${MIGRATION_DB}/fake.log" 2>&1; then
    cat "${MIGRATION_DB}/fake.log" >&2
    echo "CHECK FAIL: накат миграций на снимок прежней схемы" >&2
    exit 1
fi
grep -E '^(MIGRATION OK|  ORM|  таблиц)' "${MIGRATION_DB}/fake.log" || true
grep '^SCHEMA:' "${MIGRATION_DB}/fake.log" | sed 's/^SCHEMA://' >"${MIGRATION_DB}/fake.log.schema.json" || true

"${PYTHON}" - "${MIGRATION_DB}/apply.log.schema.json" "${MIGRATION_DB}/fake.log.schema.json" <<'PY'
import json
import sys

with open(sys.argv[1]) as fh:
    empty = json.load(fh)
with open(sys.argv[2]) as fh:
    legacy = json.load(fh)

assert empty, 'пустая схема не получена'
assert empty == legacy, (
    'схема после --fake-initial отличается от схемы миграций: {}'.format(
        sorted(set(empty) ^ set(legacy))
    )
)
print('  схема после миграций и после --fake-initial совпадает: {} таблиц'.format(len(empty)))
PY

echo "== 4/5 адаптеры зависимостей матрицы =="
"${PYTHON}" -m zipfile -e "${WHEEL}" "${WORK}/site"
export PYTHONPATH="${WORK}/site:${BACKEND}"
export EDW_CHECK_SITE="${WORK}/site"
export EDW_REPO_ROOT="${REPO_ROOT}"

if ! "${PYTHON}" "${REPO_ROOT}/scripts/check_adapters.py" >"${WORK}/adapters.log" 2>&1; then
    cat "${WORK}/adapters.log" >&2
    echo "CHECK FAIL: адаптеры зависимостей не прошли проверку" >&2
    exit 1
fi
cat "${WORK}/adapters.log"

echo "== 5/5 контракты E1/E3, права API E4 (edw из собранного wheel) =="
"${PYTHON}" - <<'PY'
import os

import edw_contract_compat

edw_contract_compat.install()

import edw
import email_auth
import social_extra

site = os.path.realpath(os.environ['EDW_CHECK_SITE']) + os.sep
for module in (edw, email_auth, social_extra):
    path = os.path.realpath(module.__file__)
    assert path.startswith(site), '{} импортирован не из wheel: {}'.format(module.__name__, path)

print('import edw: {}'.format(os.path.dirname(edw.__file__)))
PY

export DJANGO_SETTINGS_MODULE="edw_contract_settings"

set +o errexit
"${PYTHON}" -m pytest \
    --tb=short \
    -q \
    -p no:cacheprovider \
    backend/edw/tests/contract \
    backend/edw/tests/test_term.py
STATUS=$?
set -o errexit

if [[ ${STATUS} -eq 0 ]]; then
    echo "CHECK PASS"
else
    echo "CHECK FAIL (pytest exit ${STATUS})" >&2
fi

exit ${STATUS}
