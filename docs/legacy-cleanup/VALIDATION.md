# Новая проверка очистки: 2026-11-05

## Точный исходник и результат

- Tested source: `8d8f5270fb581d7947822208fdbff65ba4cb1827`.
- Tested tree: `0c91dc42d2051a39903f57ab0e566755c0fa1c24`.
- Parent (предыдущая публикация): `3a02c052d4146c0c3d09f0df02fe4533126e0221`.
- Исходный E12 tested source: `50d26164383dc1df77795a5a079ffe2be1e2a9da` — сохранён, не переименован в новый результат.
- Последующий commit с этим отчётом — **evidence-only**, не source SHA нового runtime запуска. Не подменять им tested source.

В отдельном detached checkout с чистым tracked-деревом исполнен **второй bash-блок INSTALL.md без изменения команд**, с конкретными значениями пяти переменных-путей/SHA. Новый bootstrap создан штатным `venv`, установлены пять exact-hash build tools. Gate создал отдельные resolve/core/gate окружения. Установки офлайн; новых загрузок пакетов или использования рабочих venv не было. Runtime — Linux aarch64, CPython3.12.3, SQLite/locmem.

INSTALL document SHA256: `ee52000eccada9400a67f17dda3eb66ffbcc5bb62801b07b84c8aa31dd45a3af`.
Исполненный bash-блок SHA256: `5bb065299738beaa30d625ca5a882548b434f9b798040adb974b7afc3a55dd96`.

Подтверждающие строки из [журнала](evidence/documented-install.log):

```text
168 passed in 47.81s
3 passed in 1.84s
migrations drift: 0
SAFETY PASS
DOCUMENTED_INSTALL_EXIT=0
```

Новый runtime результат — **171 passed, 0 failures, 0 errors, 0 skips**. JUnit независимо пересчитан по testcase, IDs сверены с `scripts/safety-test-inventory.json`: дубликатов, missing/unknown cases нет. **Прежние 50 independent probes не запускались; числа 221 для этого source нет.**

## Удаления и регрессионный барьер

Удалено ровно 55 tracked-файлов из трёх согласованных целей; дополнительных удалений нет. История Git не переписана. Старый demo отсутствует в текущем source tree, но не стеретcя из истории. Его SQL/fixture содержимое не читалось для удаления и не включалось в evidence.

На exact tested source `scripts/check_clean_source.py` проверил 510 активных текстовых файлов, включая ignored-but-tracked; legacy install/import references в проверяемом scope не обнаружены. 66 исторических путей намеренно пропущены, их сохранность проверена отдельно через Git diff и SHA256SUMS. Checker — узкий текстовый regression guard, не доказательство отсутствия произвольных динамических imports.

`python3.12 -I -B scripts/test_clean_source.py`: **15 tests, OK**. Все fixtures временные и синтетические, без Django/продуктовых imports. Результат хранится отдельно от 171 runtime cases, их числа не смешиваются.

Первая рабочая проверка нового барьера вернула exit1: обнаружила ещё одну старую команду в `backend/edw/tests/contract/README.md`. Инструкция исправлена, исключение для обхода проверки не добавлялось. При review до исполнения также устранены некорректный standalone bootstrap из tools.lock и риск наследования PIP_TARGET/PYTEST_ADDOPTS. Единственный фактический documented-install запуск на зафиксированном source завершился exit0; это не скрытые повторы неудачного runtime gate.

## Новый wheel и зависимости

Wheel SHA256: **`5e53ac23a7ba59810730d7ef6103b461cc8abe83742832885f5b11a31bc05854`**, размер 1,384,769 байт. Две независимые сборки из одного snapshot + pinned bundle побайтно совпали. Это не прежний E12 wheel `31db549ed51d4b7012e401ae06c286b148ff69afdcd471577747fb33616b0c7a`.

Проверены 378 ZIP members и все 377 hash-bearing wheel RECORD entries. Installed RECORD — другой счётчик: **379/379** в каждом окружении; payload comparison — 377 files. Дубликатов и небезопасных путей ZIP нет; удалённые demo/requirements/dump/fixture не попали в wheel.

Сравнение с E12 wheel: additions/deletions members — 0; изменены только `django_edw-0.2.0.dist-info/METADATA`, `RECORD`, `top_level.txt`. Package payload, включая все 305 executable `.py/.js/.mjs/.cjs`, побайтно прежний. В METADATA прежние headers/Requires-Dist, изменён README body; из top_level.txt убран пустой namespace `requirements`. Python-код продукта, dependencies в pyproject, модели/API/миграции, старые исполняемые тесты и safety gate не менялись.

- Runtime lock: 31 distributions, SHA256 `22a3d4ff3d4d9f763dcbfb33d23400f9daeb1b6e357c46b6ce298e2ac51a8056`.
- Tools complement: 10 distributions, SHA256 `ee94977723cd264b3250b863aa07c2498df1a71ceeb79bfb65ca2b59ea0bca59` (побайтно прежний).
- От прежнего runtime lock отличается только hash EDW wheel. Новые [locks](locks/runtime.lock) не переписывают `docs/neural-analysis/locks`.
- Core: 31 locked + административный pip = 32 distributions. Gate: 41 locked + pip = 42.
- `pip check`: `No broken requirements found.` в bootstrap/core/gate.
- Миграции в новой SQLite и bulk POST/upsert/DELETE-policy smoke прошли; реальные namespace providers, импорт EDW из нового site-packages.
- InfLabs bulk: SHA `e39983cb549ddc5245e726ab26261e318964258a`, wheel hash `31a26a30dbd525ca3f3620e4deaf379112548b709076de0c0e162a9d026819d6` — без изменений.
- Frontend bundle: `388d7438f290fb82ea4900b3e3eb79b4a90463ab700eeada23275f1fdc17a907` — тот же внешний input, не новая frontend сборка.

## Независимая сверка и sanitization

Отдельный reviewer read-only проверил source/tree, сохранённые refs/log/hash/JUnit/inventory, ZIP/RECORD, новый lock и scope удаления. Тесты повторно не исполнял и venv самостоятельно не инспектировал: installed facts подтверждал по сохранённым reports. Противоречий не найдено.

До/после suite RECORD без missing/mismatch, outside-site/stub lists пустые. Дополнительно статически сравнены все 16 provider полей version/module/RECORD/METADATA для каждой из двух suites (32 значения) с pre/post payload reports — совпали. Это проверка сохранённого запуска, **не исправление общего METADATA comparison gap старого runner**.

`provenance.json` хранит раздельно hashes исходных и опубликованных артефактов. В JSON/log только точные engineering-root replacements на `<CLEANUP_RUN>`, `<CLEANUP_SOURCE>`, `<INSTALL_RUN>`, `<WHEELHOUSE>`; в XML удалён только hostname attribute. Test names/counts/timestamps/hashes не менялись. `SHA256SUMS` относится к опубликованным байтам. Исходные отчёты не перезаписывались.

Исторический `docs/neural-analysis` остался неизменным (22 checksum entries), как и `edw-inventory.json`, runtime/safety reports и `docs/_build`. Старые assertions и пакетные exclusions сохранены.

## Не проверено и остаточный риск

- Не запускались 50 independent E12 probes, старый check.sh, `npm start`, frontend build/browser suite, sdist build, extras, production migration/БД, PostgreSQL concurrency/deadlocks и внешние события/outbox.
- Не доказаны переносимость на x86_64, самостоятельная установка только из публичного Git или доступность всех exact wheels в package index. Wheelhouse и pinned bundle остаются обязательными внешними inputs.
- Сохранилось предупреждение `rest_framework.W001`: в synthetic settings PAGE_SIZE указан без DEFAULT_PAGINATION_CLASS. Migration drift при этом exit0. Не выдавать результат за «без предупреждений».
- Известные ограничения прежних runner перечислены в `../neural-analysis/LIMITATIONS.md`; их код этой очисткой не исправлялся. Старый frontend dev server/config mismatch не проверялся запуском и не исправлялся.
- Это не security audit старой истории, не выпуск новой версии, не deploy и не готовность SD. Версия distribution остаётся 0.2.0; exact source и wheel hash обязательны для различения исследовательских сборок.

Остаточный риск: принять честно суженный и протестированный библиотечный контур за готовый продукт или воспроизводимый на любой машине installation kit.
