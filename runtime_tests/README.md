# E7: real-runtime gate

`scripts/check_runtime.sh` — отдельные ворота для матрицы G0.runtime. Они не
используют `edw_contract_compat` и каталог E1-заглушек: отсутствие настоящего
пакета здесь ошибка, а не skip. Исторический `scripts/check.sh` (E1–E5.fix)
сохранён как отдельный контрактный барьер.

Что делает gate:

1. проверяет точные версии матрицы и что `bitfield`, `rest_framework_bulk`,
   `rest_framework_filters`, `rest_framework_recursive` импортируются из своих
   distributions (а не из `edw/tests/contract/stubs`), вызывает `pip check`;
2. копирует дерево исходников вне клона (во временный каталог рядом с рабочим
   пространством), собирает wheel и печатает его sha256;
3. ставит wheel в подготовленное окружение офлайн
   (`--no-index --no-deps --force-reinstall`), без сети и без исторического
   `mdm-pilot-real`;
4. сравнивает все установленные файлы `edw`/`email_auth`/`social_extra` и
   `RECORD` с содержимым wheel;
5. прогоняет эти тесты (`runtime_tests`) против установленного wheel на
   синтетической sqlite;
6. проверяет `makemigrations --check --dry-run`.

Тесты описывают: регистрацию list/detail и bulk-маршрутов, nested prefix/lookup,
bulk POST/PUT/PATCH/DELETE с правами и rollback, scoped admission
(`validate_bulk_create`), filters (обычный параметр, method filter, отрицание и
пустое значение, сохранение queryset/прав), реальные `BitField`/`RecursiveField`
и единственный корневой `Entity`. Транзакция — одна write-БД; distributed
atomicity не заявляется.
