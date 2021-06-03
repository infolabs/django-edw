import { combineReducers } from 'redux';

import {actionTypes as actionTypesEntities} from '../constants/Entities';
import {actionTypes as actionTypesDropdown} from '../constants/Dropdown';

import {Dropdowns, items, loading} from './entities.js';


function dropdowns(state = new Dropdowns({}), action) {
  switch (action.type) {
    case actionTypesEntities.LOAD_ENTITIES:
      return new Dropdowns(action.json);
    case actionTypesDropdown.TOGGLE_DROPDOWN:
      return state.toggle(action.dropdown_name);
    case actionTypesDropdown.SELECT_DROPDOWN:
      return state.select(action.dropdown_name, action.selected);
    default:
      return state;
  }
}

const initialViewComponentState = {
  data: {},
  currentView: null,
};


function viewComponents(state = initialViewComponentState, action) {
  switch (action.type) {
    case actionTypesEntities.SET_DATA_VIEW_COMPONENTS:
      return {...state, data: action.data};
    case actionTypesEntities.SET_CURRENT_VIEW:
      return {...state, currentView: action.currentView};
    default:
      return state;
  }
}


const initialDetailState = {
  data: {},
  loading: false,
  visible: false,
};


function detail(state = initialDetailState, action) {
  switch (action.type) {
    case actionTypesEntities.LOAD_ENTITY:
      return {...state, data: action.json, loading: false, visible: true};
    case actionTypesEntities.NOTIFY_LOADING_ENTITY:
      return {...state, loading: true};
    case actionTypesEntities.HIDE_VISIBLE_DETAIL:
      return {...state, visible: false};
    case actionTypesEntities.DO_NOTHING:
      return {...state, loading: false, visible: true};
    default:
      return state;
  }
}


const entities = combineReducers({
  items,
  dropdowns,
  loading,
  viewComponents,
  detail,
});

export default entities;
