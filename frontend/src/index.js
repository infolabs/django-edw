import 'todomvc-app-css/index.css';
import React from 'react';
import { render } from 'react-dom';
import configureStore from './store/configureStore';
import Root from './containers/Root';

// => returns compiled css code from style.less, resolves imports and url(...)s
var css = require("!style!raw!less!./less/styles.less");

const store = configureStore();

console.log(Urls['edw:term\u002Dtree']('json') + "?data_mart_pk=1");

render(
  <Root store={store} />,
  document.getElementById('root')
);
