import {
    LOAD_ITEM,
    LOAD_ENTITY_ITEM,
    LOAD_ENTITIES,
    NOTIFY_LOADING,
    NOTIFY_LOADING_ENTITIES,
    HIDE_ENTITY_DESC,
    LOAD_TREE,
    RELOAD_TREE,
    TOGGLE_ITEM,
    RESET_ITEM,
    RESET_BRANCH,
    SHOW_ENTITY_DESC,
    SHOW_INFO,
    HIDE_INFO,
    TOGGLE_DROPDOWN,
    SELECT_DROPDOWN,
    RECACHE_RATE,
    NOTIFY_LOADING_ENTITIE_ITEM
} from '../constants/TermsTree'


function reCache(url) {
    const recache = Math.round(new Date().getTime() / RECACHE_RATE);
    return url+'?_='+recache
}

function getTermsTree(type, mart_id, selected = []) {
  let url = Urls['edw:data-mart-term-tree'](mart_id, 'json');
  url = reCache(url);

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
  }));
}

export function getTermsItem(url) {
  return fetch(reCache(url), {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: LOAD_ITEM,
    json: json,
  }));
}

export function getEntityItem(url) {
  return fetch(reCache(url), {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: LOAD_ENTITY_ITEM,
    json: json,
  }));
}

function opts2gets(options = {}) {
  let gets = '',
      i = 0;
  for (let key in options) {
    let value = options[key];
    if (typeof value == 'array')
      value = value.join()
    gets += '&' + key + '=' + value;
    i++;
  }
  return gets;
}

export function getEntities(mart_id, subj_ids=[], options = {}) {
  let url = Urls['edw:data-mart-entity-list'](mart_id, 'json');
  url = reCache(url);
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
    type: LOAD_ENTITIES,
    json: json,
    request_options: options
  }));
}

export function notifyLoading() {
  return {
    type: NOTIFY_LOADING
  };
}

export function notifyLoadingEntities() {
  return {
    type: NOTIFY_LOADING_ENTITIES
  };
}

export function loadTree(mart_id, selected = []) {
  return getTermsTree(LOAD_TREE, mart_id, selected);
}

export function reloadTree(mart_id, selected = []) {
  return getTermsTree(RELOAD_TREE, mart_id, selected);
}

export function toggle(term = {}) {
  return {
    type: TOGGLE_ITEM,
    term: term
  };
}

export function resetItem(term = {}) {
  return {
    type: RESET_ITEM,
    term: term
  };
}

export function resetBranch(term = {}) {
  return {
    type: RESET_BRANCH,
    term: term
  };
}

export function showDescription(entity_id = null) {
  return {
    type: SHOW_ENTITY_DESC,
    entity_id: entity_id
  };
}

export function hideDescription(entity_id = null) {
  return {
    type: HIDE_ENTITY_DESC,
    entity_id: entity_id
  };
}

export function showInfo(term = {}) {
  return {
    type: SHOW_INFO,
    term: term
  };
}

export function hideInfo(term = {}) {
  return {
    type: HIDE_INFO,
    term: term
  };
}

export function toggleDropdown(dropdown_name = "") {
  return {
    type: TOGGLE_DROPDOWN,
    dropdown_name: dropdown_name
  };
}

export function selectDropdown(dropdown_name = "", selected = "") {
  return {
    type: SELECT_DROPDOWN,
    dropdown_name: dropdown_name,
    selected: selected
  };
}
