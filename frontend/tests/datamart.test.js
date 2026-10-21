/*
 * Smoke-тест витрины DataMart: полный путь инициализации виджета
 * (BaseRoot -> DataMart -> Entities -> Tile -> Paginator/Statistics/Aggregation).
 */
import assert from 'node:assert/strict';

import React from 'react';

import BaseRoot from 'components/BaseRoot';

import {
  ENTITY_NAMES,
  ENTRY_POINT_ID,
  entryPoints,
} from './fixtures';
import {createEdwStore, fakeDomAttrs, renderWithStore} from './harness';


export default function dataMartTest() {
  const store = createEdwStore();

  const markup = renderWithStore(store, React.createElement(BaseRoot, {
    store,
    dom_attrs: fakeDomAttrs({
      'data-entry-points': JSON.stringify(entryPoints),
      'data-selected-entry-point-id': String(ENTRY_POINT_ID),
    }),
  }));

  // Каркас витрины.
  assert.match(markup, /class="row ex-datamart"/, 'витрина DataMart не отрисовалась');
  assert.match(markup, /main-col__top maincol-top/, 'верхняя панель витрины не отрисовалась');

  // Сущности витрины в шаблоне «плитка».
  assert.match(markup, /class="entities ex-tiles"/, 'шаблон плитки не выбран');
  assert.ok(
    markup.includes(ENTITY_NAMES.first),
    'сущность витрины отсутствует в разметке'
  );
  assert.ok(
    markup.includes('7700000001'),
    'характеристика сущности потерялась при рендере плитки'
  );

  // Заголовок группы (extra.group_size) и групповой счётчик.
  assert.ok(
    markup.includes('Группа «Бета»'),
    'заголовок группы сущностей не отрисовался'
  );
  assert.match(markup, /class="ex-digit"/, 'счётчик группы не отрисовался');

  // Панель управления: переключатель вида, сортировка, лимит, статистика.
  assert.match(markup, /class="ex-inline"/, 'переключатель вида не отрисовался');
  assert.ok(markup.includes('Плитка'), 'вариант отображения «Плитка» отсутствует');
  assert.ok(markup.includes('по названию'), 'список сортировки не отрисовался');
  assert.match(markup, /class="maincol-top__col ex-statistic"/, 'блок статистики не отрисовался');
  // В офлайн-тестах gettext тождественный, поэтому в разметке исходная строка.
  assert.match(markup, /1 - 10 from 45/, 'статистика диапазона неверна');
  assert.match(markup, /class="ex-catalog-pagination"/, 'пагинатор не отрисовался');

  // Агрегации из meta.aggregation.
  assert.match(markup, /class="ex-aggregation-attrs"/, 'агрегации витрины не отрисовались');

  // Фасеты витрины.
  assert.match(markup, /class="terms-tree"/, 'фасеты витрины не отрисовались');

  return 'datamart';
}
