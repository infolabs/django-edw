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
    SET_PREV_TAGGED_ITEMS,
} from '../constants/TermsTree';
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton';
import getUrl from '../utils/getUrl';
import uniFetch from '../utils/uniFetch';


const getTermsTree = (type, mart_id, selected = []) => dispatch => {
  let url = getUrl('edw:data-mart-term-tree', [mart_id, 'json']);
  url = reCache(url);

  if (selected && selected.length > 0)
    url += '&selected=' + selected.join();

  return uniFetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
  }).then(response => response.json()).then(json => {
    dispatch({type, json});
  });
};


export const getTerm = url => dispatch => {
  uniFetch(reCache(url), {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
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

  const globalStore = Singleton.getInstance();
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
  dispatch({type: TOGGLE_FILTERS});
};


export function toggleTerm(term = {}) {
  return dispatch => {
    dispatch({
      type: TOGGLE_TERM,
      term: term,
    });
  };
}


export function resetTerm(term = {}) {
  return dispatch => {
    dispatch({
      type: RESET_TERM,
      term: term,
    });
  };
}


export function resetBranch(term = {}) {
  return dispatch => {
    dispatch({
      type: RESET_BRANCH,
      term: term,
    });
  };
}


export function showInfo(term = {}) {
  return dispatch => {
    dispatch({
      type: SHOW_INFO,
      term: term,
    });
  };
}


export function hideInfo(term = {}) {
   return dispatch => {
    dispatch({
      type: HIDE_INFO,
      term: term,
    });
  };
}


export const setPrevTaggedItems = () => dispatch => {
  dispatch({type: SET_PREV_TAGGED_ITEMS});
};
