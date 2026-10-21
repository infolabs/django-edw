// EDW frontend entry point (react-redux, React 18.3).
//
// Полифиллы es6-promise/isomorphic-fetch больше не подключаются: офлайн-дерево
// зависимостей их не содержит, а целевые браузеры React 18.3 поддерживают
// Promise и fetch нативно.
//
// Стили подключаются обычным import: сборщик (webpack style-loader или esbuild
// плагин) сам компилирует less и вставляет результат в документ.
import './less/styles.less';

import React from 'react';
import {createRoot} from 'react-dom/client';
import configureStore from 'store/configureStore';
import Root from 'components/Root';

import Singleton from 'utils/singleton';

const ROOT_PROP = '_edwReactRoot';

const globalStore = Singleton.getInstance();

const data_marts = document.getElementsByClassName('ex-data-mart');

for (let i = data_marts.length - 1; i >= 0; i--) {
  const data_mart = data_marts[i],
        store = configureStore(),
        dom_attrs = data_mart.attributes;

  let alias = dom_attrs.getNamedItem('data-store-alias');
  if (!alias) {
    const mart_id = dom_attrs.getNamedItem('data-selected-entry-point-id');
    if (mart_id)
      alias = `data_mart_${mart_id.value}`;
  } else {
    alias = alias.value;
  }
  globalStore[alias] = store;

  // createRoot вместо устаревшего ReactDOM.render. Повторная инициализация
  // того же контейнера (повторная вставка скрипта, hot reload) переиспользует
  // уже созданный root, чтобы не плодить дубли деревьев.
  const root = data_mart[ROOT_PROP] || createRoot(data_mart);
  data_mart[ROOT_PROP] = root;
  root.render(<Root store={store} dom_attrs={dom_attrs} />);
}
