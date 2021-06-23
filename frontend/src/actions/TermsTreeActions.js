import {
    LOAD_TERM,
    LOAD_TERMS_TREE,
    RELOAD_TERMS_TREE,
    TOGGLE_FILTERS,
    TOGGLE_TERM,
    RESET_TERM,
    RESET_BRANCH,
    SHOW_INFO,
    HIDE_INFO,
    NOTIFY_LOADING_TERMS,
} from '../constants/TermsTree';
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton';


const globalStore = new Singleton();

/*
Функция для получения дерева терминов
:param type: Тип вызванного действия
:param mart_id: Id витрины данных
:param selected: Массив выбранных терминов
*/
const getTermsTree = (type, mart_id, selected = []) => dispatch => {
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
  }).then(response => response.json()).then(json => {
    dispatch({
      type: type,
      json: json,
    })
  });
};


export const getTermsItem = url => dispatch => {
  fetch(reCache(url), {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => dispatch({
    type: LOAD_TERM,
    json: json,
  }));
};


export const notifyLoadingTerms = () => dispatch => {
  dispatch({type: NOTIFY_LOADING_TERMS});
};


export const loadTree = (mart_id, selected = [])  => {
  return getTermsTree(LOAD_TERMS_TREE, mart_id, selected);
};


export const reloadTree = (mart_id, selected = []) => {
  return getTermsTree(RELOAD_TERMS_TREE, mart_id, selected);
};


export function readTree(mart_id, selected = []) {
  const type = LOAD_TERMS_TREE;
  if (globalStore.initial_trees && globalStore.initial_trees[mart_id]) {
    const json = globalStore.initial_trees[mart_id];
    return dispatch => {
      dispatch({ type, json });
    };
  } else {
    return getTermsTree(type, mart_id, selected);
  }
}

export const toggleFilters = () => dispatch => {
  dispatch({type: TOGGLE_FILTERS})
};

export function toggleTerm(term = {}) {
  return dispatch => {
    dispatch({
      type: TOGGLE_TERM,
      term: term
    });
  };
}


export function resetTerm(term = {}) {
  return dispatch => {
    dispatch({
      type: RESET_TERM,
      term: term
    });
  };
}


export function resetBranch(term = {}) {
  return dispatch => {
    dispatch({
      type: RESET_BRANCH,
      term: term
    });
  };
}


export function showInfo(term = {}) {
  return dispatch => {
    dispatch({
      type: SHOW_INFO,
      term: term
    });
  };
}


export function hideInfo(term = {}) {
   return dispatch => {
    dispatch({
      type: HIDE_INFO,
      term: term
    });
  };
}
