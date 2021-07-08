import { combineReducers } from 'redux';
import * as dropdownConsts from 'constants/Dropdown';
import * as entityConsts from 'constants/Entities';

/* Entities */

class EntitiesManager {
  constructor(json = {}, request_options = {}) {
    this.objects = this.json2objects(json);
    this.meta = this.json2meta(json, request_options);
    this.loading = false;
    if (json && json.results && json.results.meta)
      this.component = json.results.meta.view_component;
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
      'options': {},
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
            'options': modes,
          };
    this.ordering = new Dropdown(ordering_options);

    // Limits
    const default_limit = data_mart.limit || 40;
    const max_limit = data_mart.max_limit || null;
    const multipliers = [2, 5, 10, 20];
    const options = {
      [data_mart.limit]: data_mart.limit,
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
      'options': options,
    };
    this.limits = new Dropdown(limit_options);

    // ViewComponents
    const components = data_mart.view_components,
          component_options = {
            'request_var': 'view_component',
            'selected': components[json.results.meta.view_component],
            'options': components,
          };
    this.view_components = new Dropdown(component_options);
  }

  toggle(name) {
    // eslint-disable-next-line consistent-this
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
    // eslint-disable-next-line consistent-this
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


class Descriptions {
  constructor() {
    this.opened = {};
    this.groups = {};
  }

  show(id) {
    this.opened = {};
    this.opened[id] = true;
    return Object.assign(new Descriptions(), this);
  }

  hide(id) {
    // eslint-disable-next-line consistent-this
    let ret = this;
    if (this.opened[id]) {
      this.opened = {};
      ret = Object.assign(new Descriptions(), this);
    }
    return ret;
  }

  load(json) {
    if (json.extra && json.extra.group_size)
      this.groups[json.id] = json;
    else
      this[json.id] = json;
    return Object.assign(new Descriptions(), this);
  }
}


export function items(state = new EntitiesManager(), action) {
  switch (action.type) {
    case entityConsts.NOTIFY_LOADING_ENTITIES:
      state.loading = true;
      return Object.assign(new EntitiesManager(), state);
    case entityConsts.LOAD_ENTITIES:
      const newState = new EntitiesManager(action.json, action.request_options);
      if (action.append && newState.meta.offset !== state.meta.offset)
        newState.objects = [...state.objects, ...newState.objects];
      return newState;
    default:
      return state;
  }
}


export function dropdowns(state = new Dropdowns({}), action) {
  switch (action.type) {
    case entityConsts.LOAD_ENTITIES:
      return new Dropdowns(action.json);
    case dropdownConsts.TOGGLE_DROPDOWN:
      return state.toggle(action.dropdown_name);
    case dropdownConsts.SELECT_DROPDOWN:
      return state.select(action.dropdown_name, action.selected);
    default:
      return state;
  }
}


export function loading(state = false, action) {
  switch (action.type) {
    case entityConsts.NOTIFY_LOADING_ENTITIES:
      return true;
    case entityConsts.LOAD_ENTITIES:
      return false;
    default:
      return state;
  }
}


function loadingItems(state = {}, action) {
    switch (action.type) {
        case entityConsts.NOTIFY_LOADING_ENTITY:
            return Object.assign({}, state, {[action.id]: true});
        default:
          return state;
    }
}


function descriptions(state = new Descriptions(), action) {
  switch (action.type) {
    case entityConsts.SHOW_ENTITY_DESC:
      return state.show(action.entity_id);
    case entityConsts.HIDE_ENTITY_DESC:
      return state.hide(action.entity_id);
    case entityConsts.LOAD_ENTITY:
      return state.load(action.json);
    default:
      return state;
  }
}


const initialDetailState = {
  data: {},
  loading: false,
  visible: false,
};


const detail = (state = initialDetailState, action) => {
  switch (action.type) {
    case entityConsts.LOAD_ENTITY:
      return {...state, data: action.json, loading: false, visible: true};
    case entityConsts.NOTIFY_LOADING_ENTITY:
      return {...state, loading: true};
    case entityConsts.HIDE_VISIBLE_DETAIL:
      return {...state, visible: false};
    case entityConsts.DO_NOTHING:
      return {...state, loading: false, visible: true};
    default:
      return state;
  }
};

const entities = combineReducers({
    items,
    dropdowns,
    descriptions,
    loading,
    loadingItems,
    detail, // native
});


export default entities;
