import { createStore, applyMiddleware } from 'redux';
import ReactThunk from 'redux-thunk'
import rootReducer from '../../reducers';


const configureStore = () => {
  return createStore(
      rootReducer,
      applyMiddleware(ReactThunk)
  );
};

export default configureStore
