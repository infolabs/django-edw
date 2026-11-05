# Сборка и тесты фронтенда django-edw (после E5)

## Офлайн-сборка (по умолчанию)

```bash
cd frontend
NODE_PATH=/home/agent/workspace/venvs/edw-frontend/node_modules node scripts/build.mjs
```

* сборщик — esbuild из предсобранного дерева зависимостей; `npm install` не нужен;
* результат — `backend/edw/static/edw/js/bundle.js` (минифицированный IIFE, CSS
  вставляется в документ при инициализации, как раньше делал webpack style-loader);
* сборка детерминирована: тот же вход даёт побайтно тот же выход;
* `npm run build` — тот же скрипт, `npm run build:webpack` — сборка через
  `webpack.config.js`, если в окружении есть webpack и полный набор devDependencies.

## Офлайн-тесты

```bash
cd frontend
NODE_PATH=/home/agent/workspace/venvs/edw-frontend/node_modules node scripts/test.mjs
```

Smoke-тесты (`frontend/tests/`) рендерят через `react-dom/server`, без DOM и сети:
дерево терминов и фасеты, витрину DataMart целиком (`BaseRoot` → `DataMart` →
`Entities` → плитка → пагинатор, статистика, агрегации). Итоговая строка
`TESTS passed=N failed=M` разбирается в `scripts/check.sh`.

## Граница проверки

Единственный актуальный путь изолированной установки backend и его runtime-проверки
описан в корневом INSTALL.md. Он использует закреплённый внешний bundle как вход
wheel-сборки и не запускает эти frontend-команды.

Приведённые выше команды — отдельные developer-операции над подготовленным
frontend-окружением. Старый scripts/check.sh не является актуальной полной проверкой
ветки: его migration stage и зависимость от прежнего host environment имеют известные
ограничения. Успех backend gate не означает полной браузерной приёмки frontend.

## Офлайн-заглушки отсутствующих пакетов

`react-google-maps`, `react-yandex-maps` и `color` объявлены в `package.json`, но
отсутствуют в предсобранном офлайн-дереве. `scripts/buildlib.mjs` подставляет
вместо них модули из `frontend/src/vendor/` **только если пакет не установлен**;
при полном наборе зависимостей используется настоящий пакет и карты рендерятся
штатно. В офлайн-сборке карта деградирует до пустого контейнера той же высоты,
остальная витрина работает.

`marked` в офлайн-дереве — версия 12 (ESM, именованный экспорт), в
`package.json` объявлена ^0.3.5 (CJS). `src/utils/marked.js` выбирает доступную
форму экспорта, поэтому исходники работают с обеими версиями.
