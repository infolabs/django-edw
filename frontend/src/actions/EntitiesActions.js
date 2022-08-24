import {
  LOAD_ENTITY_INFO,
  NOTIFY_LOADING_ENTITIES,
  NOTIFY_LOADING_ENTITY,
  LOAD_ENTITIES,
  SHOW_ENTITY_DESC,
  HIDE_ENTITY_DESC,
  APPEND_NOT_GROUP_PARAM_TO_META,
  SAVE_UNEXPANDED_GROUP_TERMS,
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
import {getTermsTree} from './TermsTreeActions'
import {LOAD_TERMS_TREE, RELOAD_TERMS_TREE} from "../constants/TermsTree";
import {setAlike} from "../utils/locationHash";


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
      }).then(response => response.json()).then(json =>
        dispatch({type: LOAD_ENTITY_INFO, json}));
    }
  };
}


const loadingEntity = id => dispatch => {
  dispatch({type: NOTIFY_LOADING_ENTITY, id});
};

// count sent requests so as to match last response with selected terms
let inFetch = 0;

export function getEntities(params) {
  const {mart_id, template_name, unexpandedGroupTerms} = params,
    subj_ids = params.subj_ids || [],
    options_arr = params.options_arr || [],
    append = params.append || false,
    closeGroup = params.closeGroup || false;

  let options_obj = params.options_obj || {};

  if (PLATFORM === NATIVE && !append) {
    const scrollToTop = globalStore.scrollToTop;
    scrollToTop && scrollToTop();
  }

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

    // save terms on group expansion, the param is only set when expandGroup is called
    if (unexpandedGroupTerms && Array.isArray(unexpandedGroupTerms))
      dispatch({type: SAVE_UNEXPANDED_GROUP_TERMS, unexpandedGroupTerms});

    // restore terms on group close, clear saved if no 'alike' in request options
    const unexpanded = getState() && getState().entities && getState().entities.unexpandedGroupTerms;
    if (unexpanded) {
      if (closeGroup)
        options_obj.terms = unexpanded;
      if (unexpanded.length && !options_obj.alike)
        dispatch({type: SAVE_UNEXPANDED_GROUP_TERMS, unexpandedGroupTerms: []});
    }

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
        stateDataMartId = stateMeta.data_mart?.id,
        responseDataMartId = json.results.meta.data_mart.id,
        stateMetaOrdering = stateMeta.ordering,
        responseMetaOrdering = json.results.meta.ordering,
        stateMetaViewComponent = stateMeta.view_component,
        responseMetaViewComponent = json.results.meta.view_component,
        stateMetaGroupTermsIds = stateMeta.alike?.group_terms_ids || [],
        responseMetaGroupTermsIds = json.results.meta.alike?.group_terms_ids || [];

      if (!compareArrays(stateMetaGroupTermsIds, responseMetaGroupTermsIds)) {
        if (responseMetaGroupTermsIds.length || closeGroup) {
          const comboTerms = responseMetaGroupTermsIds.concat(options_obj.terms);
          dispatch(getTermsTree(LOAD_TERMS_TREE, mart_id, comboTerms));
        } else {
          dispatch(getTermsTree(RELOAD_TERMS_TREE, mart_id, stateMetaGroupTermsIds));
        }
      // Если изменилась сортировка или вид представления, то перезапрос не делаем
      } else if (inFetch === 0 && stateMetaOrdering === responseMetaOrdering && stateMetaViewComponent === responseMetaViewComponent &&
        stateDataMartId === responseDataMartId && stateRootLength) {
        const stateTerms = state.terms.tagged.items,
          responseTerms = json.results.meta.terms_ids;

        // if datamarts match, tree exists and it is the last response in the queue
        // and it mismatches with the selected terms, call the function again
        if (!compareArrays(stateTerms, responseTerms)) {
          options_obj = stateMeta.request_options;
          options_obj.terms = stateTerms;

          params = {
            ...params,
            options_obj,
          }

          dispatch(getEntities(params));
          return;
        }
      }

      if (PLATFORM === NATIVE) {
        if (!globalStore.initial_entities)
          globalStore.initial_entities = {};

        const martId = template_name === 'related' ? `${mart_id}_rel` : mart_id;

        if (!globalStore.initial_entities.hasOwnProperty(martId)) {
          globalStore.initial_entities[martId] = {
            ...json,
            notifyLoadingEntities: () => dispatch(notifyLoadingEntities()),
            getEntities: () => dispatch(getEntities({
              mart_id,
              subj_ids,
              options_obj: {...options_obj, offset: 0},
              options_arr
            }))
          };
        } else {
          globalStore.initial_entities[martId] = {
            ...globalStore.initial_entities[martId],
            ...json
          }
        }
      } else {
        !responseMetaGroupTermsIds.length && setAlike(mart_id, '');
      }

      dispatch({type: LOAD_ENTITIES, request_options: options_obj, json, append});
    });
  };
}


export function readEntities(params) {
  const {mart_id} = params,
    options_obj = params.options_obj || {},
    options_arr = params.options_arr || [];

  if (globalStore.initial_entities && globalStore.initial_entities[mart_id]) {
    const options_obj2 = optArrToObj(options_arr);
    let json = globalStore.initial_entities[mart_id];

    json.results.meta = Object.assign(json.results.meta, options_obj);
    json.results.meta = Object.assign(json.results.meta, options_obj2);

    return (dispatch) => {
      dispatch({type: LOAD_ENTITIES, json, request_options: options_obj});
    };
  }
  return getEntities(params);
}


export function expandGroup(item_id, meta) {
  const mart_id = meta.data_mart.id,
    subj_ids = meta.subj_ids;
  let request_options = meta.request_options;
  delete request_options.offset;
  delete request_options.limit;
  request_options.alike = item_id;
  setAlike(mart_id, item_id);
  const params = {
    options_obj: request_options,
    mart_id,
    subj_ids,
    unexpandedGroupTerms: request_options.terms,
  };
  return getEntities(params);
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
