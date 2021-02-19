import { createStore, applyMiddleware } from 'redux';
import rootReducer from '../reducers';
import logger from 'redux-logger';
import ReactThunk from 'redux-thunk';


let createStoreWithMiddleware = applyMiddleware(ReactThunk)(
    applyMiddleware(logger)(createStore),
    createStore
);

const configureStore = () => {

  const store = createStoreWithMiddleware(
      rootReducer
  );

  if (module.hot) {
    module.hot.accept('../reducers', () =>
      store.replaceReducer(require('../reducers').default)
    );
  }

  return store;
};

export default configureStore
