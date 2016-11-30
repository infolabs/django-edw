import { combineReducers } from 'redux';
import * as consts from '../constants/TermsTree';

/* Entities */

class EtitiesManager {
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

    const data_mart = json.results.meta.data_mart,
          modes = data_mart.ordering_modes;
    const ordering_options = {
      'request_var': 'ordering',
      'selected': modes[json.results.meta.ordering],
      'options': modes
    };
    this['ordering'] = new Dropdown(ordering_options);
    const dl = data_mart.limit || 40; // default limit
    const lopts = {}; // limit options
    lopts[dl] = dl;
    lopts[dl*2] = dl*2;
    lopts[dl*5] = dl*5;
    lopts[dl*10] = dl*10;
    lopts[dl*20] = dl*20;
    const limit = json.limit;
    const limit_options = {
      'request_var': 'limit',
      'selected': limit,
      'options': lopts
    };
    this['limits'] = new Dropdown(limit_options);
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
    if (item && item.selected != item.options[selected]) {
      item.open = false;
      item.selected = item.options[selected]
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

function items(state = new EtitiesManager(), action) {
  switch (action.type) {
    case consts.NOTIFY_LOADING_ENTITIES:
      state.loading = true;
      return Object.assign(new EtitiesManager(), state);
    case consts.LOAD_ENTITIES:
      return new EtitiesManager(action.json, action.request_options);
    default:
      return state;
  }
}

function dropdowns(state = new Dropdowns({}), action) {
  switch (action.type) {
    case consts.LOAD_ENTITIES:
      return new Dropdowns(action.json);
    case consts.TOGGLE_DROPDOWN:
      return state.toggle(action.dropdown_name);
    case consts.SELECT_DROPDOWN:
      return state.select(action.dropdown_name, action.selected);
    default:
      return state;
  }
}

function loading(state = false, action) {
  switch (action.type) {
    case consts.NOTIFY_LOADING_ENTITIES:
      return true;
    case consts.LOAD_ENTITIES:
      return false;
    default:
      return state;
  }
}

const entities = combineReducers({
    items: items,
    dropdowns: dropdowns
})

export default entities;
