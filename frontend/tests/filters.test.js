/*
 * Smoke-тест фасетов: панель Filters (переключатель фильтров + дерево
 * терминов внутри) на состоянии из реальных редьюсеров terms/entities.
 */
import assert from 'node:assert/strict';

import React from 'react';

import Filters from 'components/Filters';

import {ENTRY_POINT_ID, TERM_NAMES, entryPoints} from './fixtures';
import {createEdwStore, renderWithStore} from './harness';


export default function filtersTest() {
  const store = createEdwStore();

  const markup = renderWithStore(store, React.createElement(Filters, {
    entry_points: entryPoints,
    entry_point_id: ENTRY_POINT_ID,
  }));

  // Кнопка-переключатель фасетов.
  assert.match(markup, /class="ex-btn-group visible-xs"/, 'панель фасетов не отрисовалась');
  assert.match(markup, /class="fa fa-filter"/, 'иконка фильтра не отрисовалась');

  // В свернутом состоянии дерево скрыто CSS-классом, но остаётся в разметке.
  assert.match(markup, /class="hidden-xs"/, 'свернутые фасеты потеряли класс hidden-xs');
  assert.match(markup, /class="terms-tree"/, 'дерево терминов внутри фасетов не отрисовалось');
  assert.ok(
    markup.includes(TERM_NAMES.it),
    'термин с выбранным семантическим правилом отсутствует в фасетах'
  );

  // Раскрытое состояние: filters.active = true убирает hidden-xs.
  store.dispatch({type: 'TOGGLE_FILTERS'});
  const opened = renderWithStore(store, React.createElement(Filters, {
    entry_points: entryPoints,
    entry_point_id: ENTRY_POINT_ID,
  }));

  assert.doesNotMatch(opened, /class="hidden-xs"/, 'раскрытые фасеты остались скрытыми');
  assert.match(opened, /class="fa fa-times"/, 'кнопка закрытия фасетов не отрисовалась');
  assert.match(opened, /class="terms-tree"/, 'дерево терминов пропало в раскрытых фасетах');

  return 'filters';
}
