#!/usr/bin/env bash
#
# E1/E2/E4/E5: характеризационная проверка контрактов django-edw, упаковки,
# матрицы зависимостей, миграций, прав API и отсутствия удалённых в Django
# 5.0/5.1 вызовов (E5.fix).
#
# 1. сверяет pyproject.toml с целевой матрицей G0.1 из edw-inventory.json;
# 2. собирает wheel из pyproject.toml (PEP 517, --no-isolation, без сети)
#    и проверяет, что wheel и editable-сборка экспортируют пакеты edw,
#    email_auth, social_extra, а не backend.edw, и не тянут sandbox;
# 3. прогоняет миграции: makemigrations --check --dry-run (drift),
#    накат на пустую sqlite и накат через --fake-initial на синтетический
#    снимок прежней схемы (таблицы без миграций);
# 4. проверяет адаптеры зависимостей на офлайн-стеке матрицы;
# 5. проверяет фронтенд: React 18 createRoot, отсутствие оператора :: и поиска
#    DOM-узла по инстансу, smoke-тесты рендера и сборку production-бандла
#    через предсобранный node_modules (esbuild, без npm install);
# 6. статический барьер: в продуктовом коде нет имён, удалённых в Django 5.0/5.1
#    (timezone.utc, UserManager.make_random_password), а замены на месте;
# 7. прогоняет контрактные тесты E1/E3/E5.fix, права API E4 (edw.rest.permissions,
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

echo "== 1/8 матрица зависимостей G0.1 =="
if ! PYTHONPATH="${BACKEND}" DJANGO_SETTINGS_MODULE="edw_contract_settings" \
        "${PYTHON}" -c 'from edw.tests.contract import matrix; raise SystemExit(matrix.main())'; then
    echo "CHECK FAIL: pyproject.toml расходится с матрицей G0.1" >&2
    exit 1
fi

echo "== 2/8 сборка wheel (PEP 517) =="
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

echo "== 3/8 проверка editable =="
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

echo "== 4/8 миграции (drift, пустая sqlite, снимок прежней схемы) =="
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

echo "== 5/8 адаптеры зависимостей матрицы =="
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

echo "== 6/8 frontend: React 18 createRoot, refs, smoke-тесты и production-бандл =="

FRONTEND_DIR="${REPO_ROOT}/frontend"
EDW_NODE_MODULES="${EDW_NODE_MODULES:-/home/agent/workspace/venvs/edw-frontend/node_modules}"
NODE_BIN="${NODE_BIN:-node}"

frontend_fail() {
    echo "CHECK FAIL: $*" >&2
    exit 1
}

if ! command -v "${NODE_BIN}" >/dev/null 2>&1; then
    frontend_fail "не найден node (${NODE_BIN})"
fi
if [[ ! -d "${EDW_NODE_MODULES}/react" || ! -d "${EDW_NODE_MODULES}/esbuild" ]]; then
    frontend_fail "нет предсобранного frontend node_modules в ${EDW_NODE_MODULES}"
fi

# Сборка и тесты берут пакеты только из предсобранного дерева: npm install
# не вызывается ни здесь, ни внутри scripts/build.mjs / scripts/test.mjs.
export NODE_PATH="${EDW_NODE_MODULES}"
export EDW_NODE_MODULES

# 6.1 Исходники: ни оператора привязки ::, ни поиска DOM-узла по инстансу.
if grep -rIn --include='*.js' -E '(^|[^:[:alnum:]_$])::[[:alpha:]_$]' "${FRONTEND_DIR}/src" >"${WORK}/bindings.log" 2>&1; then
    cat "${WORK}/bindings.log" >&2
    frontend_fail "в frontend/src остались привязки через оператор ::"
fi

if grep -rIn --include='*.js' 'findDOMNode' "${FRONTEND_DIR}/src" >"${WORK}/finddomnode.log" 2>&1; then
    cat "${WORK}/finddomnode.log" >&2
    frontend_fail "в frontend/src остался поиск DOM-узла по инстансу"
fi

if grep -rIn --include='*.js' -E '![a-z-]+!' "${FRONTEND_DIR}/src" >"${WORK}/inlineloaders.log" 2>&1; then
    cat "${WORK}/inlineloaders.log" >&2
    frontend_fail "в frontend/src остались inline-цепочки загрузчиков"
fi

if ! grep -q "from 'react-dom/client'" "${FRONTEND_DIR}/src/index.js" \
        || ! grep -q 'createRoot' "${FRONTEND_DIR}/src/index.js"; then
    frontend_fail "frontend/src/index.js не переведён на createRoot"
fi
if grep -qE "ReactDOM\.render\(|from 'react-dom'" "${FRONTEND_DIR}/src/index.js"; then
    frontend_fail "frontend/src/index.js всё ещё использует legacy ReactDOM.render"
fi
echo "  исходники: 0 привязок ::, 0 поисков DOM-узла по инстансу, index.js на createRoot"

# 6.2 package.json: React/ReactDOM по матрице G0.1 (цель 18.3) и скрипты сборки.
if ! "${NODE_BIN}" - "${FRONTEND_DIR}/package.json" <<'JS'
const pkg = require(process.argv[2]);
const problems = [];
const deps = Object.assign({}, pkg.dependencies, pkg.devDependencies);

const checkReact = (name) => {
  const raw = deps[name];
  const match = /^[\^~]?(\d+)\.(\d+)(\.\d+)?/.exec(raw || '');
  if (!match) {
    problems.push(`${name}: версия не указана (${raw || 'нет'})`);
    return;
  }
  const major = Number(match[1]);
  const minor = Number(match[2]);
  if (major !== 18 || minor < 3)
    problems.push(`${name}: ожидается 18.3+, в package.json ${raw}`);
};

checkReact('react');
checkReact('react-dom');

for (const script of ['build', 'test']) {
  if (!pkg.scripts || !pkg.scripts[script])
    problems.push(`package.json: нет scripts.${script}`);
}

if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}

console.log(`  package.json: react ${deps.react}, react-dom ${deps['react-dom']}, scripts build/test на месте`);
JS
then
    frontend_fail "package.json не соответствует цели React 18.3"
fi

# 6.3 webpack.config.js: пути от __dirname, TerserPlugin, без dev-server client.
if ! "${NODE_BIN}" --check "${FRONTEND_DIR}/webpack.config.js" >"${WORK}/webpack-syntax.log" 2>&1; then
    cat "${WORK}/webpack-syntax.log" >&2
    frontend_fail "webpack.config.js не разбирается"
fi
if ! grep -q 'TerserPlugin' "${FRONTEND_DIR}/webpack.config.js"; then
    frontend_fail "webpack.config.js не подключает TerserPlugin"
fi
if ! grep -q 'path.resolve(__dirname' "${FRONTEND_DIR}/webpack.config.js"; then
    frontend_fail "webpack.config.js не считает пути от __dirname"
fi
if ! grep -q "static', 'edw', 'js'" "${FRONTEND_DIR}/webpack.config.js"; then
    frontend_fail "webpack.config.js не собирает бандл в backend/edw/static/edw/js"
fi
if grep -q '/app/' "${FRONTEND_DIR}/webpack.config.js"; then
    frontend_fail "webpack.config.js содержит зашитые пути деплоя (/app/...)"
fi
if grep -q 'webpack-dev-server' "${FRONTEND_DIR}/webpack.config.js"; then
    frontend_fail "webpack.config.js подключает клиент dev-server"
fi
if grep -qE '\bloaders[[:space:]]*:' "${FRONTEND_DIR}/webpack.config.js"; then
    frontend_fail "webpack.config.js использует устаревший ключ loaders:"
fi
echo "  webpack.config.js: path.resolve(__dirname), TerserPlugin, без dev-server client и loaders:"

# 6.4 smoke-тесты рендера: дерево терминов, фасеты, витрина DataMart.
set +o errexit
"${NODE_BIN}" "${FRONTEND_DIR}/scripts/test.mjs" >"${WORK}/frontend-tests.log" 2>&1
FRONTEND_TESTS_STATUS=$?
set -o errexit
cat "${WORK}/frontend-tests.log"
if [[ ${FRONTEND_TESTS_STATUS} -ne 0 ]]; then
    frontend_fail "smoke-тесты фронтенда (exit ${FRONTEND_TESTS_STATUS})"
fi

TESTS_LINE="$(grep -E '^TESTS passed=[0-9]+ failed=[0-9]+$' "${WORK}/frontend-tests.log" | tail -n 1 || true)"
[[ -n "${TESTS_LINE}" ]] || frontend_fail "не удалось разобрать результат smoke-тестов"
TESTS_PASSED="${TESTS_LINE#TESTS passed=}"
TESTS_PASSED="${TESTS_PASSED%% *}"
TESTS_FAILED="${TESTS_LINE##*failed=}"
if [[ "${TESTS_FAILED}" -ne 0 ]]; then
    frontend_fail "smoke-тесты фронтенда: провалов ${TESTS_FAILED}"
fi
if [[ "${TESTS_PASSED}" -lt 3 ]]; then
    frontend_fail "smoke-тестов меньше трёх (${TESTS_PASSED})"
fi

# 6.5 production-бандл: детерминированная сборка в backend/edw/static/edw/js.
set +o errexit
"${NODE_BIN}" "${FRONTEND_DIR}/scripts/build.mjs" "${WORK}/bundle-a.js" >"${WORK}/build-a.log" 2>&1
BUILD_A=$?
"${NODE_BIN}" "${FRONTEND_DIR}/scripts/build.mjs" >"${WORK}/build-main.log" 2>&1
BUILD_MAIN=$?
set -o errexit
cat "${WORK}/build-main.log"
if [[ ${BUILD_A} -ne 0 ]]; then
    cat "${WORK}/build-a.log" >&2
    frontend_fail "production-бандл не собрался (exit ${BUILD_A})"
fi
if [[ ${BUILD_MAIN} -ne 0 ]]; then
    frontend_fail "production-бандл не собрался в backend/edw/static/edw/js (exit ${BUILD_MAIN})"
fi

BUNDLE="${REPO_ROOT}/backend/edw/static/edw/js/bundle.js"
[[ -s "${BUNDLE}" ]] || frontend_fail "сборка не создала ${BUNDLE}"
if ! "${NODE_BIN}" --check "${BUNDLE}" >"${WORK}/bundle-syntax.log" 2>&1; then
    cat "${WORK}/bundle-syntax.log" >&2
    frontend_fail "production-бандл не разбирается как JavaScript"
fi

# Детерминированность: тот же вход — тот же побайтный выход.
BUNDLE_A_SHA="$(sha256sum "${WORK}/bundle-a.js" | cut -d' ' -f1)"
BUNDLE_SHA="$(sha256sum "${BUNDLE}" | cut -d' ' -f1)"
if [[ "${BUNDLE_A_SHA}" != "${BUNDLE_SHA}" ]]; then
    frontend_fail "сборка недетерминирована: sha256 ${BUNDLE_A_SHA} != ${BUNDLE_SHA}"
fi

# Клиент dev-server не должен попадать в production-бандл.
for marker in 'webpack-dev-server' 'webpack/hot' 'WebSocketClient' 'sockjs'; do
    if grep -q "${marker}" "${BUNDLE}"; then
        frontend_fail "в production-бандле найден маркер dev-server: ${marker}"
    fi
done
if ! grep -q 'createRoot' "${BUNDLE}"; then
    frontend_fail "production-бандл не содержит createRoot"
fi
if ! grep -q 'ex-data-mart' "${BUNDLE}"; then
    frontend_fail "production-бандл не содержит инициализацию виджета"
fi

BUNDLE_SIZE="$(wc -c <"${BUNDLE}" | tr -d ' ')"
if [[ "${BUNDLE_SIZE}" -lt 100000 ]]; then
    frontend_fail "production-бандл подозрительно мал: ${BUNDLE_SIZE} байт"
fi

# Бандл должен исполняться: без node-глобалов (require/module) и с вставкой
# скомпилированных less-стилей на инициализации входа.
if ! "${NODE_BIN}" "${FRONTEND_DIR}/scripts/check-bundle.mjs" "${BUNDLE}" >"${WORK}/bundle-load.log" 2>&1; then
    cat "${WORK}/bundle-load.log" >&2
    frontend_fail "production-бандл не исполняется"
fi
cat "${WORK}/bundle-load.log"

echo "  бандл: backend/edw/static/edw/js/bundle.js, ${BUNDLE_SIZE} байт, sha256 ${BUNDLE_SHA:0:16}, без dev-server client"

echo "== 7/8 статический барьер удалённых API Django 5.0/5.1 =="

# E5.fix: E6 нашёл в продукте два вызова API, удалённых в целевом стеке:
#   * django.utils.timezone.utc — удалён в Django 5.0 (замена: datetime.timezone.utc);
#   * UserManager.make_random_password() — удалён в Django 5.1
#     (замена: django.utils.crypto.get_random_string).
# Шаблон намеренно не ловит допустимые замены datetime.timezone.utc и
# datetime_timezone.utc: левее `timezone` не должно быть `_`, `.` или буквы.
# Используется ERE (grep -E), поэтому негативный lookbehind записан как группа.
REMOVED_API_RE='(^|[^.A-Za-z0-9_])timezone[[:space:]]*\.[[:space:]]*utc|timezone[[:space:]]+import[[:space:]]+utc|make_random_password'

removed_api_scan=()
for package in edw email_auth social_extra; do
    if [[ -d "${BACKEND}/${package}" ]]; then
        removed_api_scan+=("${BACKEND}/${package}")
    fi
done

if grep -rInE --include='*.py' --exclude-dir=tests --exclude-dir=__pycache__ \
        "${REMOVED_API_RE}" "${removed_api_scan[@]}" >"${WORK}/removed-api.log" 2>&1; then
    cat "${WORK}/removed-api.log" >&2
    echo "CHECK FAIL: в продуктовом коде остались API, удалённые в Django 5.0/5.1" >&2
    exit 1
fi
# Проверка самих замен: они обязаны быть на месте, а не просто удалены.
if ! grep -q 'datetime_timezone\.utc' "${BACKEND}/edw/utils/dateutils.py"; then
    echo "CHECK FAIL: dateutils не переведён на datetime.timezone.utc" >&2
    exit 1
fi
if ! grep -q 'get_random_string' "${BACKEND}/edw/forms/auth.py"; then
    echo "CHECK FAIL: forms/auth.py не переведён на django.utils.crypto.get_random_string" >&2
    exit 1
fi
echo "  продуктовый код: 0 вызовов timezone.utc и make_random_password, замены на месте"

echo "== 8/8 контракты E1/E3/E5.fix, права API E4 (edw из собранного wheel) =="
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
