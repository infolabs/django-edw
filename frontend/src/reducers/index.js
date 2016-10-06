import { combineReducers } from 'redux';
import todos from './todos';
import terms from './terms';

const rootReducer = combineReducers({
  todos,
  terms
});

export default rootReducer;
