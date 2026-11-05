# Изолированная установка и проверка EDW на Django 5.2

Это единственный актуальный документированный путь для исследовательской ветки. Он собирает **текущий точный commit**, устанавливает wheel в новые venv и проверяет обязательный контур на синтетической SQLite. Он не запускает сервер и не настраивает production-проект.

## Предварительные условия

1. Отдельный чистый checkout нужного commit этой ветки. Запишите полный 40-символьный SHA; не используйте изменяемое имя ветки как доказательство проверенной версии.
2. CPython **3.12.3** с `venv` и штатным `ensurepip`. Проверенная машина — Linux aarch64. Другие платформы, включая x86_64 neural, требуют собственных совместимых колёс и отдельной проверки; aarch64 wheels нельзя переносить на x86_64.
3. Локальный **wheelhouse** с проверенными зависимостями и tools. Исторические списки точных версий/хешей: `docs/neural-analysis/locks/runtime.lock` и `tools.lock`. Старый runtime.lock содержит hash **старого** EDW wheel, поэтому его нельзя применять для установки пересобранного текущего EDW. Gate сам сформирует новый runtime.lock с hash текущего wheel.
4. В wheelhouse обязательно должен быть `djangorestframework_bulk-0.3.0a1-py3-none-any.whl` с SHA256 `31a26a30dbd525ca3f3620e4deaf379112548b709076de0c0e162a9d026819d6`. Исходник: https://github.com/infolabs/django-rest-framework-bulk/tree/e39983cb549ddc5245e726ab26261e318964258a . Обычный bulk `0.2.1` не заменяет этот provider.
5. Предподготовленный frontend bundle с SHA256 `388d7438f290fb82ea4900b3e3eb79b4a90463ab700eeada23275f1fdc17a907`, согласно `scripts/safety-inputs.json`. Это внешний build input; он не находится в Git. Этот документ не утверждает, что любая новая frontend-сборка даст те же байты.
6. Новый каталог результатов **вне checkout и вне рабочих окружений/БД**. Gate оставляет артефакты для проверки и не очищает переданный корневой каталог.

Без wheelhouse или bundle остановитесь. Их публичная доступность не гарантирована этой веткой. `pip install .` с произвольным индексом, установка extras или использование исторического check.sh не являются эквивалентной заменой.

## Единственная последовательность

В новом shell задайте свои абсолютные пути и точный SHA. Сетевые загрузки пакетов в этой последовательности отключены.

```bash
export EDW_REPO=/absolute/path/to/disposable/django-edw
export EDW_EXPECTED_HEAD=FULL_40_HEX_COMMIT
export EDW_WHEELHOUSE=/absolute/path/to/verified/wheelhouse
export EDW_BUNDLE=/absolute/path/to/verified/bundle.js
export EDW_RUN_BASE=/absolute/path/to/new-run-parent
```

Затем из корня checkout выполните:

```bash
set -euo pipefail
: "${EDW_REPO:?}" "${EDW_EXPECTED_HEAD:?}" "${EDW_WHEELHOUSE:?}" "${EDW_BUNDLE:?}" "${EDW_RUN_BASE:?}"
test "$(pwd -P)" = "$(realpath "$EDW_REPO")"
test "$(git rev-parse HEAD)" = "$EDW_EXPECTED_HEAD"
test -z "$(git status --porcelain=v1 --untracked-files=no)"
python3.12 -I -B -c 'import sys; assert sys.version_info[:3] == (3, 12, 3)'
python3.12 -I -B scripts/check_clean_source.py

# Не наследуем перенаправление pip install, pytest options или чужие settings.
# Например, PIP_TARGET и PYTEST_ADDOPTS могли бы направить запись вне нового run.
for name in ${!PIP_@} ${!PYTEST_@} ${!PYTHON@} ${!EDW_SAFETY_@}; do
  unset "$name"
done
unset EDW_RUNTIME_DB EDW_CONTRACT_DB DJANGO_SETTINGS_MODULE VIRTUAL_ENV
export PIP_CONFIG_FILE=/dev/null PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1

mkdir -p "$EDW_RUN_BASE"
export EDW_INSTALL_RUN="$(mktemp -d "$EDW_RUN_BASE/edw-install.XXXXXXXX")"
mkdir -p "$EDW_INSTALL_RUN/tmp"
export TMPDIR="$EDW_INSTALL_RUN/tmp"
python3.12 -I -B -m venv "$EDW_INSTALL_RUN/bootstrap-env"
# tools.lock — дополнение к runtime.lock, не самостоятельная closure.
# Для bootstrap выбираем только полную Python3.12 build closure, без pytest/Django/EDW.
python3.12 -I -B - <<'PY'
import os, pathlib, re
source = pathlib.Path(os.environ['EDW_REPO']) / 'docs/neural-analysis/locks/tools.lock'
wanted = {'build', 'packaging', 'pyproject-hooks', 'setuptools', 'wheel'}
selected = {}
for line in source.read_text().splitlines():
    match = re.fullmatch(r'([a-z0-9-]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})', line)
    if match and match[1] in wanted:
        if match[1] in selected:
            raise SystemExit('duplicate build pin')
        selected[match[1]] = line
if set(selected) != wanted:
    raise SystemExit('incomplete build closure')
path = pathlib.Path(os.environ['EDW_INSTALL_RUN']) / 'build.lock'
with path.open('x') as handle:
    handle.write('\n'.join(selected[name] for name in sorted(selected)) + '\n')
PY
"$EDW_INSTALL_RUN/bootstrap-env/bin/python" -m pip install \
  --no-index --find-links "$EDW_WHEELHOUSE" --require-hashes \
  --no-cache-dir --no-compile --no-input \
  -r "$EDW_INSTALL_RUN/build.lock"
"$EDW_INSTALL_RUN/bootstrap-env/bin/python" -m pip check

# Только ignored build input; существующий файл не перезаписываем.
python3.12 -I -B - <<'PY'
import hashlib, json, os, pathlib
repo = pathlib.Path(os.environ['EDW_REPO']).resolve()
source = pathlib.Path(os.environ['EDW_BUNDLE'])
expected = json.loads((repo / 'scripts/safety-inputs.json').read_text())['frontend_bundle']
if not source.is_file() or source.is_symlink():
    raise SystemExit('bundle must be a regular non-symlink file')
data = source.read_bytes()
if hashlib.sha256(data).hexdigest() != expected['sha256']:
    raise SystemExit('bundle hash mismatch')
target = repo / expected['path']
if target.exists() or target.is_symlink():
    if target.is_symlink() or not target.is_file() or target.read_bytes() != data:
        raise SystemExit('existing bundle is not the pinned regular file')
else:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(data)
print('pinned bundle verified')
PY

export EDW_SAFETY_EXPECTED_HEAD="$EDW_EXPECTED_HEAD"
export EDW_SAFETY_WHEELHOUSE="$EDW_WHEELHOUSE"
export EDW_SAFETY_PYTHON="$EDW_INSTALL_RUN/bootstrap-env/bin/python"
export EDW_SAFETY_RUN_BASE="$EDW_INSTALL_RUN/gate-runs"
bash scripts/check_safety.sh 2>&1 | tee "$EDW_INSTALL_RUN/gate.log"
python3.12 -I -B scripts/check_clean_source.py
```

Не задавайте `EDW_RUNTIME_DB` на существующую БД. Не подключайте тестовые settings к серверу. Не запускайте pytest в архивном `docs/neural-analysis/probes/` без отдельной подготовки — его hook может писать рядом с архивным evidence.

## Ожидаемый результат и состав окружений

Успех — exit 0 и последняя строка `SAFETY PASS`, а не просто успешный импорт Django. Gate:

- требует exact HEAD и чистое tracked-дерево;
- собирает wheel дважды из Git snapshot + pinned bundle и сравнивает SHA256;
- разрешает обязательные зависимости офлайн и фиксирует выбранные hashes;
- устанавливает отдельные **core-env** (обязательные пакеты) и **gate-env** (пакеты + tools);
- выполняет `pip check`, проверяет происхождение импорта из нового site-packages и RECORD;
- применяет миграции в синтетической SQLite и проверяет bulk/API smoke;
- запускает 168 product cases и 3 write-alias cases с exact inventory, JUnit и post-suite evidence;
- проверяет migration drift и сохраняет `summary.json`, `locks/`, `dist/`, `junit/`, install/payload reports.

Пути итогового run и нового wheel hash выводятся как `SAFETY EVIDENCE=...` и `SAFETY WHEEL_SHA256=...`. Новые lock-файлы и hashes относятся к этому запуску, не заменяют исторический E12-пакет. Изменение README меняет metadata wheel, даже когда runtime Python-код прежний.

Рабочие venv/БД не используются и не изменяются. Bootstrap/core/gate environments остаются внутри нового run. Удалять результаты можно только после отдельного решения владельца; автоматической очистки shared directories эта инструкция не содержит.

## Границы

Эта проверка не доказывает production upgrade, PostgreSQL concurrency/deadlocks, внешние события/outbox, совместимость extras и произвольных расширений. Ограничения существующего runner (в том числе неполное сравнение provider METADATA после suite) сохранены в `docs/neural-analysis/LIMITATIONS.md`; успешный запуск не устраняет их автоматически.

Тестовый frontend input не подтверждает полную браузерную приёмку. Статика и optional modules присутствуют в wheel не как гарантия готового приложения. Для встраивания в SD нужны отдельные доменная модель, доступы, конфигурация, миграционная стратегия и эксплуатационные проверки.
