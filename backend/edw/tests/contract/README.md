# E1/E4/E5: характеризационные тесты контрактов django-edw

Исторический синтетический offline-контур E1/E4/E5 для характеризации ядра.
Единственный актуальный путь изолированной установки и runtime-проверки описан
в корневом `INSTALL.md`; он использует новые окружения и настоящие providers.

Старый `scripts/check.sh` привязан к прежнему host environment и migration checker,
который ожидает только начальную миграцию. Он не является текущей полной проверкой
ветки. Его прежние assertions, stubs и compatibility harness сохранены как
характеризационные материалы, а не как замена современного runtime gate.

## Состав

* `app/` — синтетическое приложение `EDW_APP_LABEL = 'edw_contracts'`:
  ровно один корневой `ContractEntity(BaseEntity)`, его полиморфный подкласс,
  `Term`, `DataMart`, `Customer`, `DataMartPermission` и relation-модели.
* `app/migrations/` — начальная `0001_initial` и добавленная позднее
  `0002_fastdeleteprobe_protectedprobe_unknowneffectprobe` для synthetic safety cases.
  Старое ожидание «только 0001» в `scripts/check_migrations.py` не является
  подтверждённым migration path текущего контура.
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
* `test_removed_api_contract.py` (E5.fix) — регрессия по API, удалённым в
  Django 5.0/5.1: `datetime_to_local` с UTC-конвертацией через `datetime`
  (не `django.utils.timezone.utc`), генерация пароля `RegisterUserForm` через
  `django.utils.crypto.get_random_string` (не `UserManager.make_random_password`)
  и статический барьер по всем продуктовым модулям `edw`.
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
