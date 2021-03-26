import { combineReducers } from 'redux';
import entities from './entities';
import terms from './terms';


const rootReducer = combineReducers({
  entities,
  terms
});

export default rootReducer;
