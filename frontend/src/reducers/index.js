import { combineReducers } from 'redux';
import terms from './terms';
import entities from './entities';
import datamart_list from './datamart_list';


const rootReducer = combineReducers({
  terms,
  entities,
  datamart_list,
});

export default rootReducer;
