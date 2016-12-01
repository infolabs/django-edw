import * as types from '../constants/TermsTree';

const MART_ID = 4;

function getTermsTree(type, selected = []) {
  let url = Urls['edw:data-mart-term-tree'](MART_ID, 'json');

  if (selected && selected.length > 0)
    url += '?selected=' + selected.join()
  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: type,
    json: json,
  }));
}

export function getTermsItem(url) {
  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: types.LOAD_ITEM,
    json: json,
  }));
}

function opts2gets(options = {}) {
  let gets = '',
      i = 0;
  for (let key in options) {
    let prefix = i == 0 ? '?' : '&';
    let value = options[key];
    if (typeof value == 'array')
      value = value.join()
    gets += prefix + key + '=' + value;
    i++;
  }
  return gets;
}

export function getEntities(options = {}) {
  let url = Urls['edw:data-mart-entity-list'](MART_ID, 'json');
  url += opts2gets(options);

  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: types.LOAD_ENTITIES,
    json: json,
    request_options: options
  }));
}

export function notifyLoading() {
  return {
    type: types.NOTIFY_LOADING,
  };
}

export function notifyLoadingEntities() {
  return {
    type: types.NOTIFY_LOADING_ENTITIES,
  };
}

export function loadTree() {
  return getTermsTree(types.LOAD_TREE);
}

export function reloadTree(selected = []) {
  return getTermsTree(types.RELOAD_TREE, selected);
}

export function toggle(term = {}) {
  return {
    type: types.TOGGLE_ITEM,
    term: term,
  };
}

export function resetItem(term = {}) {
  return {
    type: types.RESET_ITEM,
    term: term,
  };
}

export function showInfo(term = {}) {
  return {
    type: types.SHOW_INFO,
    term: term,
  };
}

export function hideInfo(term = {}) {
  return {
    type: types.HIDE_INFO,
    term: term,
  };
}

export function toggleDropdown(dropdown_name = "") {
  return {
    type: types.TOGGLE_DROPDOWN,
    dropdown_name: dropdown_name
  };
}

export function selectDropdown(dropdown_name = "", selected = "") {
  return {
    type: types.SELECT_DROPDOWN,
    dropdown_name: dropdown_name,
    selected: selected
  };
}
