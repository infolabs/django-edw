import { combineReducers } from 'redux';
import terms from './terms';
import entities from './entities';

const rootReducer = combineReducers({
  terms,
  entities
});

export default rootReducer;
