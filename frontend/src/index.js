import React from 'react';
import { render } from 'react-dom';
import configureStore from './store/configureStore';
import Root from './containers/Root';

// => returns compiled css code from style.less, resolves imports and url(...)s

var css = require("!style!raw!less!./less/styles.less");

const rubricators = document.getElementsByClassName('ex-rubricator');

for (const rubricator of rubricators) {
  const store = configureStore(),
        dom_attrs = rubricator.attributes;
  render(
    <Root store={store} dom_attrs={dom_attrs} />,
    rubricator
  );
}

