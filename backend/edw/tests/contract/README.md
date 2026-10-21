# E1: характеризационные тесты контрактов django-edw

Синтетический offline-контур для фиксации текущего поведения ядра EDW.
Запуск:

```bash
./scripts/check.sh
```

Скрипт использует предсобранный `/home/agent/workspace/venvs/edw-modernize/bin/python`,
sqlite в памяти и locmem-кэш. `pip`/`npm install`, сеть и внешние БД не нужны.

## Состав

* `app/` — синтетическое приложение `EDW_APP_LABEL = 'edw_contracts'`:
  ровно один корневой `ContractEntity(BaseEntity)`, его полиморфный подкласс,
  `Term`, `DataMart` и relation-модели.
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

## Тестовая обвязка (вне ядра)

* `backend/edw_contract_compat.py` возвращает в процесс удалённые в Django 4+
  имена (`ugettext*`, `force_text`, `Signal(providing_args=...)`).
* `backend/edw_contract_settings.py` — минимальные настройки контура.
* `stubs/` — минимальные offline-заглушки пакетов, которых нет в окружении:
  `bitfield`, `rest_framework_bulk`, `rest_framework_filters`,
  `rest_framework_recursive`. Продукт их не использует.
* `app/apps.py` прогревает cache-флаги EDW, чтобы `AppConfig.ready()` ядра не
  обращался к БД до её создания в тестах.

## Зафиксированные известные ограничения (xfail, non-strict)

1. `BaseEntityQuerySet.semantic_filter()` фильтрует through-модель по полю
   `entity`, но автоматическая through-модель называет FK по корневой модели
   (`contractentity`) → `FieldError`.
2. Вставка третьего уровня дерева `DataMart` падает с
   `TypeError: unhashable type: 'DataMart'`: `BaseDataMart` определяет `__eq__`
   без `__hash__`, а mptt складывает экземпляры в `set`.

Оба теста помечены `xfail(strict=False)`: после исправления ядра они станут
XPASS и не сломают проверку.
