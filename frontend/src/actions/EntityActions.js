import Singleton from 'singleton-js-es6';

const globalStore = new Singleton();

import {
    LOAD_ENTITY_ITEM,
    LOAD_ENTITIES,
    NOTIFY_LOADING_ENTITIES,
    HIDE_ENTITY_DESC,
    SHOW_ENTITY_DESC,
    NOTIFY_LOADING_ENTITIE_ITEM,
    TOGGLE_DROPDOWN,
    SELECT_DROPDOWN,
} from '../constants/TermsTree'
import reCache from '../utils/reCache';


export function getEntityItem(data) {
  return (dispatch, getState) => {
    if ( !getState().entities.loadingItems[data.id] ) {
      dispatch(loadingEntityItem(data.id));

      fetch(reCache(data.entity_url), {
          method: 'get',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
        }).then(response => response.json()).then(json => dispatch({
          type: LOAD_ENTITY_ITEM,
          json: json,
        }));
      }

    }
}

function loadingEntityItem(id) {
    return dispatch => {
          dispatch({
          type: NOTIFY_LOADING_ENTITIE_ITEM,
            id
          })
    }
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

export function getEntities(mart_id, subj_ids=[], options_obj = {}, options_arr = []) {
    return dispatch => {
        let url = Urls['edw:data-mart-entity-list'](mart_id, 'json');
        url = reCache(url);
        if (subj_ids.length) {
            subj_ids.join();
            url = reCache(Urls['edw:data-mart-entity-by-subject-list'](mart_id, subj_ids, 'json'));
          }
          url += opts2gets(options_obj);

          if (options_arr.length) {
            url += "&" + options_arr.join("&");
          }

          fetch(url, {
            credentials: 'include',
            method: 'get',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
          }).then(response => response.json()).then(json => dispatch({
            type: LOAD_ENTITIES,
            json: json,
            request_options: options_obj
          }));
    };
}

export function readEntities(mart_id, subj_ids=[], options_obj = {}, options_arr = []) {
  if (globalStore.initial && globalStore.initial[mart_id]) {
    let json = globalStore.initial[mart_id];
    json.results.meta = Object.assign(json.results.meta, options_obj);
    return dispatch => {
        dispatch({
            type: LOAD_ENTITIES,
            json: json,
            request_options: options_obj
        });
    };
  } else {
    return getEntities(mart_id, subj_ids, options_obj, options_arr);
  }

}

export function showDescription(entity_id = null) {
    return dispatch => {
        dispatch({
            type: SHOW_ENTITY_DESC,
            entity_id: entity_id
        })
    }
}

export function hideDescription(entity_id = null) {
  return dispatch => {
    dispatch({
      type: HIDE_ENTITY_DESC,
      entity_id: entity_id
    })
  }
}

export function toggleDropdown(dropdown_name = "") {
  return dispatch => {
    dispatch({
      type: TOGGLE_DROPDOWN,
      dropdown_name: dropdown_name
    })
  }
}

export function selectDropdown(dropdown_name = "", selected = "") {
  return dispatch => {
    dispatch({
      type: SELECT_DROPDOWN,
      dropdown_name: dropdown_name,
      selected: selected
    })
  }
}

export function notifyLoadingEntities() {
    return dispatch => {
        dispatch({
            type: NOTIFY_LOADING_ENTITIES
        })
    }
}
