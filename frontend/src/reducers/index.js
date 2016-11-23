import { combineReducers } from 'redux';
import todos from './todos';
import terms from './terms';
import entities from './entities';

const rootReducer = combineReducers({
  todos,
  terms,
  entities
});

export default rootReducer;
