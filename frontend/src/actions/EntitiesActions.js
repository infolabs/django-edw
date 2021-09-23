import {
  LOAD_ENTITY_INFO,
  NOTIFY_LOADING_ENTITIES,
  NOTIFY_LOADING_ENTITY,
  LOAD_ENTITIES,
  SHOW_ENTITY_DESC,
  HIDE_ENTITY_DESC,
  APPEND_NOT_GROUP_PARAM_TO_META,
} from '../constants/Entities';
import {
  TOGGLE_DROPDOWN,
  SELECT_DROPDOWN,
} from '../constants/Dropdown';
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton';
import getUrl from '../utils/getUrl';
import uniFetch from '../utils/uniFetch';
import compareArrays from '../utils/compareArrays';
import {NATIVE, PLATFORM} from "../constants/Common";


const globalStore = Singleton.getInstance();

export function opts2gets(options = {}) {
  let gets = '';
  for (let key in options) {
    let value = options[key];
    if (Array.isArray(value))
      value = value.join();
    gets += '&' + key + '=' + value;
  }
  return gets;
}


export function optArrToObj(arr) {
  let ret = {};
  if (!arr.length)
    return ret;
  for (const arg of arr) {
    if (arg.includes('=')) {
      const query = arg.split('=');
      ret[query[0]] = query[1];
    }
  }
  return ret;
}


export function getEntityInfo(data, meta = false) {
  data.entity_url = data.entity_url.replace(/\.html$/, '.json');
  let url = reCache(data.entity_url);

  if (meta) {
    const opts = {
      'alike': true,
      'data_mart_pk': meta.data_mart.id,
      'terms': meta.terms_ids,
      'subj': meta.subj_ids,
    };
    url += opts2gets(opts);
  }

  return (dispatch, getState) => {
    if (!getState().entities.loadingItems[data.id]) {
      dispatch(loadingEntity(data.id));
      uniFetch(url, {
        method: 'get',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      }).then(response => response.json()).then(json => dispatch({
        type: LOAD_ENTITY_INFO,
        json: json,
      }));
    }
  };
}


const loadingEntity = id => dispatch => {
  dispatch({type: NOTIFY_LOADING_ENTITY, id});
};

// count sent requests so as to match last response with selected terms
let inFetch = 0;

export function getEntities(mart_id, subj_ids = [], options_obj = {}, options_arr = [], append = false) {
  return (dispatch, getState) => {
    // ignore more than 3 simultaneous requests from tree
    const currentMeta = getState().entities.items.meta,
      treeRootLength = getState().terms.tree.root.children.length,
      currentDataMartId = currentMeta.data_mart && currentMeta.data_mart.id;

    if (treeRootLength && currentDataMartId === mart_id && inFetch > 3)
      return;

    // set computed initial terms if not set
    const terms = getState().terms,
      tagged = terms.tagged.items,
      options_obj2 = optArrToObj(options_arr);
    if (treeRootLength && !options_obj.terms && (!options_obj2.terms || !options_obj2.terms.length))
      options_obj.terms = tagged;

    let url = getUrl('edw:data-mart-entity-list', [mart_id, 'json']);
    url = reCache(url);
    if (subj_ids.length) {
      subj_ids.join();
      url = reCache(getUrl('edw:data-mart-entity-by-subject-list', [mart_id, subj_ids, 'json']));
    }
    url += opts2gets(options_obj);

    if (options_arr.length)
      url += '&' + options_arr.join('&');

    options_arr.map(item => {
      const itemMatch = item.match(/(.*?)=(\d{1,})/);
      if (itemMatch)
        options_obj[itemMatch[1]] = itemMatch[2];
    });

    inFetch++;

    uniFetch(url, {
      credentials: 'include',
      method: 'get',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    }).then(response => response.json()).then(json => {

      inFetch--;
      const state = getState(),
        stateRootLength = state.terms.tree.root.children.length,
        stateMeta = state.entities.items.meta,
        stateDataMartId = stateMeta.data_mart && stateMeta.data_mart.id,
        responseDataMartId = json.results.meta.data_mart.id,
        stateMetaOrdering = stateMeta.ordering,
        responseMetaOrdering = json.results.meta.ordering,
        stateMetaViewComponent = stateMeta.view_component,
        responseMetaViewComponent = json.results.meta.view_component;

      // Если изменилась сортировка или вид представления, то перезапрос не делаем
      if (inFetch === 0 && stateMetaOrdering === responseMetaOrdering && stateMetaViewComponent === responseMetaViewComponent &&
        stateDataMartId === responseDataMartId && stateRootLength) {
        const stateTerms = state.terms.tagged.items,
          responseTerms = json.results.meta.terms_ids;

        // if datamarts match, tree exists and it is the last response in the queue
        // and it mismatches with the selected terms, call the function again
        if (!compareArrays(stateTerms, responseTerms)) {
          options_obj = stateMeta.request_options;
          options_obj.terms = stateTerms;
          dispatch(getEntities(mart_id, subj_ids, options_obj, options_arr));
          return;
        }
      }

      if (PLATFORM === NATIVE) {
        globalStore.edwDispatch = dispatch;

        if (!globalStore.initial_entities)
          globalStore.initial_entities = {};

        // json.limit === 6 - template_name is related
        if (!globalStore.initial_entities.hasOwnProperty(mart_id) && json.limit !== 6) {
          globalStore.initial_entities[mart_id] = {
            ...json,
            getEntities: getEntities(mart_id, subj_ids,options_obj, options_arr)
          };
        }
      }

      dispatch({type: LOAD_ENTITIES, request_options: options_obj, json, append});
    });
  };
}


export function readEntities(mart_id, subj_ids = [], options_obj = {}, options_arr = []) {
  if (globalStore.initial_entities && globalStore.initial_entities[mart_id]) {
    const options_obj2 = optArrToObj(options_arr);
    let json = globalStore.initial_entities[mart_id];

    json.results.meta = Object.assign(json.results.meta, options_obj);
    json.results.meta = Object.assign(json.results.meta, options_obj2);

    return (dispatch) => {
      dispatch({type: LOAD_ENTITIES, json, request_options: options_obj});
    };
  } else {
    return getEntities(mart_id, subj_ids, options_obj, options_arr);
  }
}


export function expandGroup(item_id, meta) {
  const mart_id = meta.data_mart.id,
    subj_ids = meta.subj_ids;
  let request_options = meta.request_options;
  delete request_options.offset;
  delete request_options.limit;
  request_options.alike = item_id;
  return getEntities(mart_id, subj_ids, request_options);
}


export const showDescription = (entity_id = null) => dispatch => {
  dispatch({type: SHOW_ENTITY_DESC, entity_id})
};

export const hideDescription = (entity_id = null) => dispatch => {
  dispatch({type: HIDE_ENTITY_DESC, entity_id});
};

export const toggleDropdown = (dropdown_name = '') => dispatch => {
  dispatch({type: TOGGLE_DROPDOWN, dropdown_name});
};

export const selectDropdown = (dropdown_name = '', selected = '') => dispatch => {
  dispatch({type: SELECT_DROPDOWN, dropdown_name, selected});
};

export const notifyLoadingEntities = () => dispatch => {
  dispatch({type: NOTIFY_LOADING_ENTITIES});
};

export const setEntitiesNotGroup = not_group => dispatch => {
  dispatch({type: APPEND_NOT_GROUP_PARAM_TO_META, not_group})
};
