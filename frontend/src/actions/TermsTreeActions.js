import * as types from '../constants/TermsTree';

const TREE_RECACHE_RATE = 1;
const ENTRIES_RECACHE_RATE = 60000;

function getTermsTree(type, mart_id, selected = []) {
  let url = Urls['edw:data-mart-term-tree'](mart_id, 'json');
  const recache = Math.round(new Date().getTime() / TREE_RECACHE_RATE)

  url += '?_=' + recache
  if (selected && selected.length > 0)
    url += '&selected=' + selected.join();

  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: type,
    json: json,
    selected: selected,
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

export function getEntities(mart_id, subj_ids=[], options = {}) {
  const recache = Math.round(new Date().getTime() / ENTRIES_RECACHE_RATE);
  options['_'] = recache;

  let url = Urls['edw:data-mart-entity-list'](mart_id, 'json');
  if (subj_ids.length) {
    subj_ids.join();
    url = Urls['edw:data-mart-entity-by-subject-list'](mart_id, subj_ids, 'json');
  }
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

export function loadTree(mart_id, selected = []) {
  return getTermsTree(types.LOAD_TREE, mart_id, selected);
}

export function reloadTree(mart_id, selected = []) {
  return getTermsTree(types.RELOAD_TREE, mart_id, selected);
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


export function showDescription(entity_id = null) {
  return {
    type: types.SHOW_ENTITY_DESC,
    entity_id: entity_id,
  };
}

export function hideDescription(entity_id = null) {
  return {
    type: types.HIDE_ENTITY_DESC,
    entity_id: entity_id,
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
