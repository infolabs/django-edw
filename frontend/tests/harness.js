/*
 * Помощники smoke-тестов: реальные редьюсеры EDW + серверный рендер React 18.
 *
 * Тесты не поднимают DOM и не ходят в сеть: дерево, фасеты и витрина
 * рендерятся через react-dom/server на состоянии, собранном теми же
 * редьюсерами, что работают в браузере.
 */
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {Provider} from 'react-redux';
import {createStore} from 'redux';

import rootReducer from 'reducers';
import {LOAD_TERMS_TREE} from 'constants/TermsTree';
import {LOAD_ENTITIES} from 'constants/Entities';

import {entitiesPayload, requestOptions, termsTree} from './fixtures';


export function createEdwStore() {
  const store = createStore(rootReducer);
  store.dispatch({type: LOAD_TERMS_TREE, json: termsTree});
  store.dispatch({
    type: LOAD_ENTITIES,
    json: entitiesPayload,
    request_options: requestOptions,
  });
  return store;
}


export function renderWithStore(store, element) {
  return renderToStaticMarkup(
    React.createElement(Provider, {store}, element)
  );
}


// Подмена NamedNodeMap контейнера .ex-data-mart для проверки полного пути
// инициализации виджета (BaseRoot читает атрибуты из DOM).
export function fakeDomAttrs(attrs) {
  return {
    getNamedItem(name) {
      return Object.prototype.hasOwnProperty.call(attrs, name)
        ? {name, value: attrs[name]}
        : null;
    },
  };
}
