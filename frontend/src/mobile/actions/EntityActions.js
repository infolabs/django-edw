import {
    LOAD_ENTITY_ITEM,
    LOAD_ENTITIES,
    NOTIFY_LOADING_ENTITIES,
    HIDE_ENTITY_DESC,
    SHOW_ENTITY_DESC,
    NOTIFY_LOADING_ENTITIE_ITEM,
    TOGGLE_DROPDOWN,
    SELECT_DROPDOWN,
} from '../constants/TermsTree';
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton';
import compareArrays from '../utils/compareArrays';


const instance = Singleton.getInstance();

const opts2gets = (options = {}) => {
  let gets = '';
  for (let key in options) {
    let value = options[key];
    if (Array.isArray(value))
      value = value.join();
    gets += '&' + key + '=' + value;
  }
  return gets;
};

const optArrToObj = arr => {
  let ret = {};
  if (!arr.length)
    return ret;
  for (const arg of arr) {
    if (arg.includes("=")) {
      const query = arg.split("=");
      ret[query[0]] = query[1];
    }
  }
  return ret;
};

export const getEntityItem = (data, meta = false) => {
  data.entity_url = data.entity_url.replace(/\.html$/,'.json');
  let url = reCache(data.entity_url);
  if (meta) {
    const opts = {
      "alike": true,
      "data_mart_pk": meta.data_mart.id,
      "terms": meta.terms_ids,
      "subj": meta.subj_ids
    };
    url += opts2gets(opts);
  }
  return (dispatch, getState) => {
    if ( !getState().entities.loadingItems[data.id] ) {
      dispatch(loadingEntityItem(data.id));
      fetch(url, {
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
  };
};

const loadingEntityItem = id => dispatch => {
  dispatch({type: NOTIFY_LOADING_ENTITIE_ITEM, id});
};

// count sent requests so as to match last response with selected terms
let inFetch = 0;

export const getEntities = (mart_id, subj_ids=[], options_obj = {}, options_arr = []) => (dispatch, getState) => {
  // ignore more than 3 simultaneous requests from tree
  const currentMeta = getState().entities.items.meta,
        // treeRootLength = getState().terms.tree.root.children.length,
        treeRootLength = {},
        currentDataMartId = currentMeta.data_mart && currentMeta.data_mart.id;

  if (treeRootLength && currentDataMartId == mart_id && inFetch > 3)
    return;

  // set computed initial terms if not set
  const terms = getState().terms,
        tagged = terms.tagged.items,
        options_obj2 = optArrToObj(options_arr);
  if (treeRootLength && !options_obj.terms && (!options_obj2.terms || !options_obj2.terms.length))
    options_obj.terms = tagged;

  // eslint-disable-next-line no-undef
  let url = '';

  if (subj_ids.length) {
      subj_ids.join();
      // eslint-disable-next-line no-undef
      url = reCache(`${instance.Domain}${Urls['edw:data-mart-entity-by-subject-list'](mart_id, subj_ids, 'json')}`);
  } else
    url = reCache(`${instance.Domain}${Urls['edw:data-mart-entity-list'](mart_id, 'json')}`);

  url += opts2gets(options_obj);

  if (options_arr.length)
    url += "&" + options_arr.join("&");


  inFetch++;

  fetch(url, {
    credentials: 'include',
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => {
    inFetch--;
    const state = getState(),
          stateRootLength = null,
          // stateRootLength = state.terms.tree.root.children.length,
          stateMeta = state.entities.items.meta,
          stateDataMartId = stateMeta.data_mart && stateMeta.data_mart.id,
          responseDataMartId = json.results.meta.data_mart.id;

    instance[json.results.meta.data_mart.slug] = json;

    if (inFetch === 0 && stateDataMartId === responseDataMartId && stateRootLength) {
      const stateTerms = state.terms.tagged.items,
            responseTerms = json.results.meta.terms_ids;

      // if datamarts match, tree exists and it is the last response in the queue
      // and it mismatches with the selected terms, call the function again
      if (!compareArrays(stateTerms, responseTerms)) {
        options_obj = stateMeta.request_options;
        options_obj.terms = stateTerms;
        dispatch(
          getEntities(mart_id, subj_ids, options_obj)
        );
        return;
      }
    }

    dispatch({type: LOAD_ENTITIES, json: json, request_options: options_obj});
  });
};


export const readEntities = (mart_id, subj_ids=[], options_obj = {}, options_arr = []) => {
  if (instance && instance[mart_id]) {
    const options_obj2 = optArrToObj(options_arr);
    let json = instance[mart_id];

    json.results.meta = Object.assign(json.results.meta, options_obj);
    json.results.meta = Object.assign(json.results.meta, options_obj2);

    return (dispatch) => {
      dispatch({type: LOAD_ENTITIES, json: json, request_options: options_obj});
    };
  } else
    return getEntities(mart_id, subj_ids, options_obj, options_arr);
};

export const expandGroup = (item_id, meta) => {
  const mart_id = meta.data_mart.id,
        subj_ids = meta.subj_ids;
  let request_options = meta.request_options;
  delete request_options["offset"];
  delete request_options["limit"];
  request_options["alike"] = item_id;
  return getEntities(mart_id, subj_ids, request_options);
};

export const showDescription = (entity_id = null) => dispatch => {
  dispatch({type: SHOW_ENTITY_DESC, entity_id: entity_id });
};

export const hideDescription = (entity_id = null) => dispatch => {
  dispatch({type: HIDE_ENTITY_DESC, entity_id: entity_id});
};

export const toggleDropdown = (dropdown_name = "") => dispatch => {
  dispatch({type: TOGGLE_DROPDOWN, dropdown_name: dropdown_name});
};

export const selectDropdown = (dropdown_name = "", selected = "") => dispatch => {
  dispatch({type: SELECT_DROPDOWN, dropdown_name: dropdown_name, selected: selected});
};

export const notifyLoadingEntities = () => dispatch => {
  dispatch({type: NOTIFY_LOADING_ENTITIES});
};
