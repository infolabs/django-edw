require('es6-promise').polyfill();
require('isomorphic-fetch');

import React from 'react';
import {render} from 'react-dom';
import configureStore from 'store/configureStore';
import Root from 'components/Root';

import Singleton from 'utils/singleton';

// => returns compiled css code from style.less, resolves imports and url(...)s
var css = require("!style!raw!less!./less/styles.less");

const globalStore = new Singleton();

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
  } else
    alias = alias.value;
  globalStore[alias] = store;

  render(
    <Root store={store} dom_attrs={dom_attrs} />,
    data_mart
  );
}
