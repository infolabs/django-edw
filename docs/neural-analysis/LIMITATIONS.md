# Границы evidence и вопросы для анализа

Статические наблюдения при подготовке передачи 2026-11-05. Не являются новым runtime-прогоном, отзывом прошлых человеческих решений или разрешением production. Код анализируемого commit `50d26164383dc1df77795a5a079ffe2be1e2a9da` не исправлялся.

## 1. Продуктовый scope

- Синтетика и SQLite, в том числе второй database alias; locmem cache. PostgreSQL locking/concurrency/deadlocks, нагрузка, distributed atomicity не проверены.
- Сохранённые миграционные проверки не доказывают upgrade реальной production schema. В synthetic test app есть миграции 0001 и 0002.
- `runtime_tests/test_safety_s1_entity.py` тестирует writable-поведение через test-only viewset. Production Entity по умолчанию остаётся read-only; нельзя выдать test endpoint за готовый write API продукта.
- Hook counters и rollback tests не равны проверке внешних событий: outbox, on_commit, повторной доставки, idempotency, exactly-once, post-view rendering и параллельных запросов.
- Нет приёмки SD-процессов ticket/SLA/dispatch/spares/maintenance. Наличие FSM mixin не заменяет реализации доменных transitions и проверки workflow.
- `auth/admin/search/task/geo` extras вне принятой обязательной матрицы. Поддержка произвольных расширений, Python/Django линий и production auth не заявляется.

## 2. Происхождение и несамодостаточность проверки

- Существующие E12 JSON/XML относятся к exact product SHA. Вновь пересчитаны только XML и hashes, тесты заново не выполнялись.
- Опубликованные JSON/XML — обозначенные производные с заменой инженерных absolute paths и удалением XML hostname. Это не byte-exact originals; оба hash уровня указаны в `provenance.json`.
- Исходники 50 probes скопированы побайтно из сохранившегося каталога проверяющего. Их current source hashes зафиксированы сейчас; отдельного независимого исторического source-hash manifest на момент старого запуска не установлено. Совпадение case IDs с JUnit не доказывает неизменность каждой строки с момента запуска.
- Предыдущий human-readable observer summary неверно разбивал 50 probes по модулям. XML даёт: `test_00_smoke=1`, `test_admission=18`, `test_delete_effects=14`, `test_r1_r2_r5=14`, `test_s1_entity_cache=3`. Общий итог 50 не меняется. Ошибочный Markdown не переписан и не включён в пакет.
- В корневых исторических runtime/safety report SHA являются ancestors, а не exact product tip. Их прежние counts не заменяют E12.
- Внешний frontend bundle и offline wheelhouse не включены. Hash locks фиксируют выбранные артефакты, но не гарантируют их доступность из публичного package index или воспроизводимость сборки из любой версии sdist.

## 3. Статические находки в проверочных инструментах

### Старый migration checker

`scripts/check_migrations.py:183–195` ожидает `applied == ['0001_initial']`, хотя synthetic app в product tip содержит также `0002_fastdeleteprobe_protectedprobe_unknowneffectprobe.py`. Старый `scripts/check.sh:171–174` вызывает этот fake-initial этап. Это статическое несоответствие; новый runtime не запускался. Не представлять старый check.sh как отдельно подтверждённо зелёный на tip.

### Старые runners изменяют файловую систему

`scripts/check_runtime.sh:43–48` удаляет caller-supplied work directory при cleanup, если KEEP не включён; дальше устанавливает wheel в подготовленный venv. `scripts/check.sh:35–40` очищает build/egg-info. Это не read-only команды. Передавать как исторический исходник, не запускать с shared/production paths. Более новый `check_safety.sh` имеет отдельные ограничения и тоже создаёт среды/БД/артефакты; для текущего статического анализа его запуск не требуется.

### Неполное post-suite сравнение provider metadata

`scripts/check_safety_env.py:819–833` сравнивает provider version, RECORD и hash модуля, но не собранный `metadata_sha256`. Нельзя утверждать, что этим кодом обнаруживается любая мутация provider METADATA. Это completeness gap инструмента, не доказательство мутации сохранённых E12-файлов.

### Независимый probe hook — writer evidence, не самостоятельный fail-closed gate

`probes/conftest.py` пишет `post-suite-session.json`. Его `pytest_sessionfinish` при ошибке записи/проверки сохраняет error report, но сам не делает успешный pytest exit ошибочным. `_post_suite_evidence` собирает `edw_modules_outside_site`, provider version и metadata_sha256, однако не все эти поля включены в comparisons. Поэтому 50 passed сами по себе не доказывают post-suite integrity.

Сохранённый `evidence/independent-post-suite.json` сообщает `ok=true`, exitstatus=0, reasons=[], outside-site=[], RECORD 379/379. При подготовке передачи отдельно сверены все 16 значений version/module/RECORD/METADATA четырёх providers с сохранённым install evidence: совпали. Эта ручная статическая сверка закрывает вопрос по указанным полям сохранённого run, но не исправляет общую слабость runner.

По умолчанию независимый harness пишет evidence рядом с `probes/`. При будущем запуске нельзя писать поверх архивного `docs/neural-analysis/evidence`: нужен отдельный run/evidence каталог и явно выбранные synthetic settings/import paths. Текущий пакет предназначен для чтения, не является командой запуска.

### Косметика

В продуктовой разнице `git diff --check` отмечает новую пустую строку EOF в `backend/edw/models/rest.py:541`. Не исправлялась, чтобы сохранить exact source pin.

## 4. История и безопасность публикации

Baseline уже достижим из существующего публичного master указанного GitHub repo. Ветка не добавляет непубликовавшуюся до этого старую историю в новый репозиторий. Новые 16 commits проверены по содержимому/метаданным ограниченным статическим review; типовые token/private-key/credential-URL утечки не подтверждены, credential-like test literals имеют synthetic назначение.

Это не всеобъемлющий security audit. Унаследованные sandbox dumps/settings/build artifacts не удалялись из истории и не объявлены безопасными для production. Git author/committer metadata сохранены как часть истории. Клинические записи, local mission outputs, credentials и транскрипты не включались и не читались в этой задаче.

## 5. Что нужно вернуть по результатам SD-анализа

- Findings с точными path/line/SHA и разделением confirmed defect / static concern / missing evidence.
- Матрицу «утверждение → тест/доказательство → ограничение».
- Отдельно application behavior и недостатки test tooling.
- Минимальный набор missing tests: production migration, PostgreSQL concurrency, permissions/cascade edge cases, external events, extensions.
- Сравнение EDW против plain Django по стоимости разработки и сопровождения конкретных SD-сценариев; не только перечень возможностей.

Не проверено этой публикацией: новые runtime результаты, production integration, security всего upstream-наследия, лицензии всех зависимостей, полноценный end-user UI и эксплуатация SD.
Остаточный риск: счесть исследовательский exact pin и успешные SQLite cases готовым промышленным SD-продуктом.
