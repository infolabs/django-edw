import React from 'react';
import { render } from 'react-dom';
import configureStore from 'store/configureStore';
import Root from 'components/Root';

// => returns compiled css code from style.less, resolves imports and url(...)s
var css = require("!style!raw!less!./less/styles.less");

const dataMarts = document.getElementsByClassName('ex-data-mart');

for (const dataMart of Array.from(dataMarts)) {
  const store = configureStore(),
        dom_attrs = dataMart.attributes;
  render(
    <Root store={store} dom_attrs={dom_attrs} />,
    data_mart
  );
}

