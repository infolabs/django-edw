import {
    LOAD_ITEM,
    LOAD_TREE,
    RELOAD_TREE,
    TOGGLE_ITEM,
    RESET_ITEM,
    RESET_BRANCH,
    SHOW_INFO,
    HIDE_INFO,
    NOTIFY_LOADING
} from '../constants/TermsTree'
import reCache from '../utils/reCache';


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

export function notifyLoading() {
  return {
    type: NOTIFY_LOADING
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
