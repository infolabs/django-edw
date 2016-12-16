import { combineReducers } from 'redux';
import terms from 'reducers/terms';
import entities from 'reducers/entities';

const rootReducer = combineReducers({
  terms,
  entities
});

export default rootReducer;
