import { createStore, compose, applyMiddleware } from 'redux';
import promise from 'redux-promise';
import { persistState } from 'redux-devtools';
import rootReducer from 'reducers';
import logger from 'redux-logger'


let createStoreWithMiddleware = applyMiddleware(promise)(applyMiddleware(logger)(createStore));

export default function configureStore(initialState) {

  const store = createStoreWithMiddleware(
      rootReducer,
      initialState
  );

  if (module.hot) {
    module.hot.accept('../reducers', () =>
      store.replaceReducer(require('../reducers').default)
    );
  }

  return store;
}
