/*
 * Smoke-тест дерева терминов (фасеты): TermsTree + TermsTreeItem +
 * TermsTreeItemInfo на состоянии из реального редьюсера terms.
 */
import assert from 'node:assert/strict';

import React from 'react';

import TermsTree from 'components/TermsTree';

import {ENTRY_POINT_ID, TERM_NAMES, entryPoints} from './fixtures';
import {createEdwStore, renderWithStore} from './harness';


export default function termsTreeTest() {
  const store = createEdwStore();

  const markup = renderWithStore(store, React.createElement(TermsTree, {
    entry_points: entryPoints,
    entry_point_id: ENTRY_POINT_ID,
  }));

  assert.match(markup, /class="terms-tree"/, 'дерево терминов не отрисовалось');
  assert.ok(
    markup.includes(TERM_NAMES.it),
    'видимый узел дерева терминов отсутствует в разметке'
  );
  assert.ok(
    markup.includes(TERM_NAMES.software),
    'дочерний термин с семантическим правилом OR не отрисовался'
  );
  assert.match(
    markup,
    /class="ex-icon-info"/,
    'иконка информации о термине не отрисовалась'
  );
  assert.match(
    markup,
    /data-slug="it"/,
    'узел дерева потерял data-slug термина'
  );

  return 'terms tree';
}
