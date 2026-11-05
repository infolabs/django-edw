# EDW: пакет для независимого анализа пригодности к Service Desk

Это ветка для анализа исходников, а не релиз, deployment или утверждение о промышленной готовности. Новые тесты, миграции и сборки при подготовке этой публикации не запускались.

## Репозиторий и два разных SHA

- Репозиторий: https://github.com/infolabs/django-edw
- Публикуемая отдельная ветка: `mission/edw-modernize`.
- **Анализируемый и ранее проверенный продуктовый commit:** `50d26164383dc1df77795a5a079ffe2be1e2a9da`.
- Tree продуктового commit: `3eec4ec3913dfea16f7fdc7296a8fbac112bfccd`.
- **Исходная база модернизации:** `25590306df82f9605ac689c36ba55d0ab98dfb65`.
- Модернизация: 16 линейных commits после базы, 256 изменённых путей, +17768/-3637 строк.
- Parent продуктового tip: `596df1c1192349e810b0bde05eaeaa07304a7aca`.
- Поверх продуктового tip добавлен только этот каталог `docs/neural-analysis/`. Поэтому SHA вершины публикационной ветки отличается от анализируемого продуктового SHA. История не переписана; продуктовый код и прежние отчёты не исправлены задним числом.
- При подготовке 2026-11-05 удалённый `master` был `530bacf27d6d2b6317d82711bf33e60725b808e5`, на два commits дальше общей базы. Эти два commits **не влиты** в исследовательскую ветку. Отдельный clone подтвердил, что вся история до базы уже достижима из публичного `master` этого репозитория.

Сравнение именно модернизации, а не расхождения с сегодняшним master:

```text
git log --reverse --oneline 25590306df82f9605ac689c36ba55d0ab98dfb65..50d26164383dc1df77795a5a079ffe2be1e2a9da
git diff --stat 25590306df82f9605ac689c36ba55d0ab98dfb65 50d26164383dc1df77795a5a079ffe2be1e2a9da
```

`provenance.json` и `SHA256SUMS` фиксируют состав передаваемого пакета. Они не являются цифровой подписью или новым тестовым запуском.

## Что предоставлено

1. Полная исходная Git-история EDW, включая 16 commits модернизации.
2. Продуктовые тесты в `runtime_tests/`, `runtime_tests_safety_alias/`, `backend/edw/tests/` и durable gate в `scripts/check_safety.sh`, `scripts/check_safety_env.py`, `scripts/safety-inputs.json`, `scripts/safety-test-inventory.json` — они уже находятся в продуктовой истории.
3. `locks/runtime.lock` и `locks/tools.lock`: точные версии и SHA256 артефактов, использованных сохранённым E12 gate.
4. `evidence/`: обезличенные производные существующих summary/install/post-suite JSON и трёх JUnit. Абсолютные пути заменены стабильными символическими корнями, hostname удалён из JUnit. Счётчики, case names, зависимости и hashes сохранены. Hash исходного файла и преобразование указаны в `provenance.json`; hash опубликованных байтов — там же и в `SHA256SUMS`.
5. `probes/`: побайтные копии 10 файлов независимых E12-проб, сохранённых проверяющим. Это отдельный тестовый harness, не часть продукта и не production settings.
6. `LIMITATIONS.md`: границы доказательств и статические находки, переданные без исправления продукта.

Не включены: сырые логи, venv, БД проверок, клинические/клиентские записи, Host state и транскрипты сессий, credentials, wheelhouse и готовые бинарные wheels. Унаследованные sandbox/demo-файлы остаются в уже публичной продуктовой истории; текущая проверка публикации не сертифицирует безопасность всего upstream-наследия.

## Зафиксированный стек и вариант bulk

`pyproject.toml` содержит декларацию зависимостей; lock-файлы содержат точную сохранённую резолюцию. Записи install report — наблюдение прежнего изолированного окружения, а не текущего production-runtime.

- Python: сохранённый E12 interpreter `3.12.3`. В `pyproject.toml` нет `requires-python`; более широкая поддержка Python не доказана.
- Django `5.2.18`; DRF `3.18.3`; django-bitfield `2.4.0`.
- django-filter `26.2`; djangorestframework-filters `1.0.0.dev2`; recursive `0.1.2`.
- django-mptt `0.20.0`; django-polymorphic `4.11.7`; django-fsm-2 `4.2.4`; nested-routers `0.95.3`; select2 `8.4.8`; filer `3.6.0`.
- EDW distribution `0.2.0`. Совпадение номера версии не гарантирует совпадение исходников или wheel.

**Использован не обычный PyPI bulk 0.2.1:**

- Репозиторий: https://github.com/infolabs/django-rest-framework-bulk
- Ветка: `modernize/django52`.
- Exact source SHA: `e39983cb549ddc5245e726ab26261e318964258a`.
- Distribution: `djangorestframework-bulk==0.3.0a1`, namespace `rest_framework_bulk`.
- Wheel SHA256: `31a26a30dbd525ca3f3620e4deaf379112548b709076de0c0e162a9d026819d6`.
- Удалённый ref bulk непосредственно проверен 2026-11-05 и совпал с этим SHA. Сам bulk не изменялся и заново не публиковался этой задачей.

EDW wheel, к которому относятся E12-результаты: `31db549ed51d4b7012e401ae06c286b148ff69afdcd471577747fb33616b0c7a`.

## Что подтверждает существующее evidence

В сохранённых JUnit непосредственно пересчитаны `testcase`, failures/errors/skipped и duplicate IDs:

- `evidence/runtime-tests.xml`: 168 тестов;
- `evidence/write-alias-tests.xml`: 3 теста;
- `evidence/independent-probes.xml`: 50 тестов;
- всего 221; failures, errors, skipped и дубликатов case ID — 0.

Продуктовые 168+3 cases совпадают с `scripts/safety-test-inventory.json`. Это **пересчёт существующих результатов**, не новый прогон. Число тестов не является исчерпывающим доказательством безопасности.

Контур: синтетические Term/DataMart/Entity, SQLite, включая второй alias, locmem cache. Проверялись admission пачки, identity, nested scope, DELETE effect set, часть каскадов/M2M/FK/MPTT, routing aliases, dynamic serializer cache и негативные случаи самого gate. Не заявляется PostgreSQL concurrency/deadlocks, production upgrade, внешние события, нагрузка или SD workflow.

Отчёты `edw-runtime-report.json` и `edw-safety-report.json` в корне репозитория исторические: они относятся соответственно к `8d78a27ea1aa4b36fb8791f08bd6298904a39b9e` и `9cd26d68cc91316481ab2b6dff336d17ddc13ad7`, а не к product tip. Для tip использовать E12 evidence в этом каталоге.

## Воспроизводимость: что ещё потребуется

Ветка пригодна для предметного статического анализа. Она **не является самодостаточным offline build/test kit**:

- Нужны wheels точного содержимого из lock-файлов; наличие всех этих файлов в публичном package index здесь не проверено.
- Gate требует ignored frontend input `backend/edw/static/edw/js/bundle.js`, SHA256 `388d7438f290fb82ea4900b3e3eb79b4a90463ab700eeada23275f1fdc17a907`. Он не tracked и не включён в публикационный пакет.
- Для совпадения старого wheel следует использовать exact product commit, а не документационный tip ветки.
- Независимые probes используют установленный EDW wheel, его synthetic contract app, prepared install evidence и отдельный E12 harness. Простое чтение или `pytest probes/` без подготовки не воспроизводит весь старый gate.
- Старые runners изменяют окружения и некоторые удаляют временные каталоги. Не запускать их в рабочем checkout/production или с произвольными shared paths. См. `LIMITATIONS.md`.

## Вопросы независимого анализа SD

1. Отделить устранение Django-несовместимости от изменений semantics API, models, permissions, cascades и migrations.
2. Проверить допуск доступа и весь effect set bulk/nested/delete; транзакционные границы, параллельные изменения, hooks/signals и внешнюю доставку событий.
3. Привязать каждое существенное утверждение к конкретному тесту; выделить SQLite-only и отсутствующие сценарии.
4. Оценить migration path, extension compatibility, точные build inputs, стоимость поддержки fork и выпуска.
5. Сравнить пользу Term/Entity/DataMart, semantic query и FSM для оборудования/НСИ с реализацией на обычном Django. Ticket/SLA/dispatch/spares/maintenance здесь не объявлены готовыми.

Лицензия EDW — BSD-3-Clause, исходный `LICENSE.txt` сохранён. Соблюдать copyright/disclaimer и ограничения endorsement. Лицензии зависимостей и готовность юридического состава релиза полностью не аудированы; эта публикация релиза не создаёт.
