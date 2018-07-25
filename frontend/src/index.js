import React from 'react';
import { render } from 'react-dom';
import configureStore from 'store/configureStore';
import Root from 'components/Root';

import Singleton from 'singleton-js-es6';

// => returns compiled css code from style.less, resolves imports and url(...)s
var css = require("!style!raw!less!./less/styles.less");

const data_marts = document.getElementsByClassName('ex-data-mart');

for (let i = data_marts.length - 1; i >= 0; i--) {
  const data_mart = data_marts[i],
        store = configureStore(),
        dom_attrs = data_mart.attributes;

  render(
    <Root store={store} dom_attrs={dom_attrs} />,
    data_mart
  );
}
