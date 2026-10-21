# E1/E4: характеризационные тесты контрактов django-edw

Синтетический offline-контур для фиксации текущего поведения ядра EDW.
Запуск:

```bash
./scripts/check.sh
```

Скрипт использует предсобранный `/home/agent/workspace/venvs/edw-modernize/bin/python`,
sqlite в памяти и locmem-кэш. `pip`/`npm install`, сеть и внешние БД не нужны.
Кроме контрактов E1/E3 `check.sh` проверяет матрицу зависимостей G0.1, миграции
(`makemigrations --check --dry-run`, накат на пустую sqlite и `--fake-initial`
на снимок прежней схемы) и адаптеры django-filer / django-filter / django-fsm-2.

## Состав

* `app/` — синтетическое приложение `EDW_APP_LABEL = 'edw_contracts'`:
  ровно один корневой `ContractEntity(BaseEntity)`, его полиморфный подкласс,
  `Term`, `DataMart`, `Customer`, `DataMartPermission` и relation-модели.
* `app/migrations/` — единственная начальная миграция контура `0001_initial`:
  позволяет проверять drift и накат схемы; прежняя схема без миграций
  эмулируется `migrate --run-syncdb` (см. `scripts/check_migrations.py`).
* `test_materialization.py` — контракт `edw/deferred.py`: один корень
  `BaseEntity`, запрет второй материализации, отсутствие pending-маппингов.
* `test_term_contract.py` — MPTT-дерево, пути, `decompress`, битовые атрибуты и
  семантические правила OR / XOR / AND.
* `test_entity_contract.py` — полиморфные выборки, type-термины, `EntityRelation`,
  `subj` / `rel` / `subj_and_rel`, `AdditionalEntityCharacteristicOrMark`.
* `test_datamart_contract.py` — дерево витрин, `active_terms_ids`,
  `entities_model`, `DataMartRelation`, субъекты связей.
* `test_rest_contract.py` — `RESTMeta`, наборы полей и эталонные представления
  сериализаторов Entity / DataMart / Term, разбор `rel`-ключей.
* `test_permissions_contract.py` (E4) — строгая семантика `edw.rest.permissions`
  (`IsReadOnly`, `IsSuperuserOrReadOnly`, `IsOwnerOr*`, владелец витрины),
  `DataMartPermission` deny-by-default и проверка прав через реальный DRF-view.
* `test_dependency_matrix.py` (E4) — `pyproject.toml` против матрицы G0.1 и
  адаптеры django-filter / django-mptt / django-fsm-2.
* `matrix.py` — единый источник целевых границ зависимостей для теста и
  первого шага `scripts/check.sh`.

## Тестовая обвязка (вне ядра)

* `backend/edw_contract_compat.py` возвращает в процесс удалённые в Django 4+
  имена (`ugettext*`, `force_text`, `Signal(providing_args=...)`).
* `backend/edw_contract_settings.py` — минимальные настройки контура;
  `EDW_CONTRACT_DB` переключает sqlite с памяти на файл для проверок миграций.
* `stubs/` — минимальные offline-заглушки пакетов, которых нет в окружении:
  `bitfield`, `rest_framework_bulk`, `rest_framework_filters`,
  `rest_framework_recursive`. Продукт их не использует.
* `app/apps.py` прогревает cache-флаги EDW, чтобы `AppConfig.ready()` ядра не
  обращался к БД до её создания в тестах.

## Бывшие известные ограничения (исправлены в E3)

1. `BaseEntityQuerySet.semantic_filter()` фильтровал through-модель по полю
   `entity`, но автоматическая through-модель называет FK по корневой модели
   (`contractentity`) → `FieldError`. Теперь имя FK определяется по модели.
2. Вставка третьего уровня дерева `DataMart` падала с
   `TypeError: unhashable type: 'DataMart'`: `BaseDataMart` определял `__eq__`
   без `__hash__`, а mptt складывает экземпляры в `set`. Теперь `__hash__`
   согласован с `__eq__`.

Оба теста идут без `xfail`: `test_semantic_filter_queryset_contract`,
`test_datamart_third_level_insertion`.
