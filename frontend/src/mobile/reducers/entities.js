import {combineReducers} from 'redux';
import {actionTypes as actionTypesEntities} from "../constants/Entities";
import {actionTypes as actionTypesDropdown} from "../constants/Dropdown";

/* Entities */

class EntitiesManager {
  constructor(json = {}, request_options = {}) {
    this.objects = this.json2objects(json);
    this.meta = this.json2meta(json, request_options);
    this.loading = false;
  }

  json2objects(json) {
    return json.results && json.results.objects || [];
  }

  json2meta(json, request_options) {
    let meta = json.results && json.results.meta || {};
    meta.count = json.count;
    meta.limit = json.limit;
    meta.offset = json.offset;
    meta.next = json.next;
    meta.previous = json.previous;
    meta.request_options = request_options;
    return meta;
  }
}

/* Dropdown */

class Dropdown {
  constructor(options) {
    let defaults = {
      'open': false,
      'request_var': '',
      'selected': '',
      'options': {}
    };
    Object.assign(this, defaults, options);
  }
}

class Dropdowns {
  constructor(json) {
    if (!(json && json.results))
      return;

    const data_mart = json.results.meta.data_mart;

    // Ordering
    const modes = data_mart.ordering_modes,
      ordering_options = {
        'request_var': 'ordering',
        'selected': modes[json.results.meta.ordering],
        'options': modes
      };
    this['ordering'] = new Dropdown(ordering_options);

    // Limits
    const default_limit = data_mart.limit || 40;
    const max_limit = data_mart.max_limit || null;
    const multipliers = [2, 5, 10, 20];
    const options = {
      [data_mart.limit]: data_mart.limit
    };
    for (const m of multipliers) {
      const o = default_limit * m;
      if (max_limit && o >= max_limit) {
        options[max_limit] = max_limit;
        break;
      }
      options[o] = o;
    }
    const limit = json.limit;
    const limit_options = {
      'request_var': 'limit',
      'selected': limit,
      'options': options
    };
    this['limits'] = new Dropdown(limit_options);

    // ViewComponents
    const components = data_mart.view_components,
      component_options = {
        'request_var': 'view_component',
        'selected': components[json.results.meta.view_component],
        'options': components
      };
    this['view_components'] = new Dropdown(component_options);
  }

  toggle(name) {
    let ret = this;
    let item = this[name];
    if (item) {
      if (!item.open) {
        for (let key in this)
          this[key].open = false;
        item.open = true;
      } else {
        item.open = false;
      }
      ret = Object.assign(new Dropdowns(), this);
    }
    return ret;
  }

  select(name, selected) {
    let ret = this;
    let item = this[name];
    if (item && item.selected !== item.options[selected]) {
      item.open = false;
      item.selected = item.options[selected];
      ret = Object.assign(new Dropdowns(), this);
    }
    return ret;
  }

  hide_all() {
    for (let key in this)
      this[key].open = false;
    return Object.assign(new Dropdowns(), this);
  }
}

const items = (state = new EntitiesManager(), action) => {
  switch (action.type) {
    case actionTypesEntities.NOTIFY_LOADING_ENTITIES:
      state.loading = true;
      return Object.assign(new EntitiesManager(), state);
    case actionTypesEntities.LOAD_ENTITIES:
      return new EntitiesManager(action.json, action.request_options);
    default:
      return state;
  }
};

const dropdowns = (state = new Dropdowns({}), action) => {
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
};

const loading = (state = false, action) => {
  switch (action.type) {
    case actionTypesEntities.NOTIFY_LOADING_ENTITIES:
      return true;
    case actionTypesEntities.LOAD_ENTITIES:
      return false;
    default:
      return state;
  }
};

const initialViewComponentState = {
  data: {},
  currentView: null
};

const viewComponents = (state = initialViewComponentState, action) => {
  switch (action.type) {
    case actionTypesEntities.SET_DATA_VIEW_COMPONENTS:
      return {...state, data: action.data};
    case actionTypesEntities.SET_CURRENT_VIEW:
      return {...state, currentView: action.currentView};
    default:
      return state;
  }
};

const entities = combineReducers({
  items,
  dropdowns,
  loading,
  viewComponents
});

export default entities;
