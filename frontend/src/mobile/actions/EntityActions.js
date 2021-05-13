import {actionTypes as actionTypesEntities} from "../constants/Entities";
import {actionTypes as actionTypesDropdown} from "../constants/Dropdown";
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton';


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

export const getEntities = (mart_id, subj_ids = [], options_obj = {}, options_arr = [], usePrevTerms = false) => (dispatch, getState) => {
  const currentItems = getState().entities.items,
        currentMeta = currentItems.meta,
        currentOffset = currentMeta.offset,
        treeRootLength = getState().terms.tree.root.children.length;

  // set computed initial terms if not set
  const terms = getState().terms,
        tagged = usePrevTerms ? terms.tagged.prevItems : terms.tagged.items,
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

  fetch(url, {
    credentials: 'include',
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => {
    if (currentOffset !== json.offset)
      json.results.objects = [...currentItems.objects, ...json.results.objects];

    instance[mart_id] = json;
    dispatch({type: actionTypesEntities.LOAD_ENTITIES, json, request_options: options_obj});
  });
};


export const readEntities = (mart_id, subj_ids=[], options_obj = {}, options_arr = []) => {
  if (instance && instance[mart_id]) {
    const options_obj2 = optArrToObj(options_arr);
    let json = instance[mart_id];

    json.results.meta = Object.assign(json.results.meta, options_obj);
    json.results.meta = Object.assign(json.results.meta, options_obj2);

    return dispatch => (
      dispatch({type: actionTypesEntities.LOAD_ENTITIES, json, request_options: options_obj})
    )
  } else
    return getEntities(mart_id, subj_ids, options_obj, options_arr);
};

export const toggleDropdown = (dropdown_name = "") => dispatch => {
  dispatch({type: actionTypesDropdown.TOGGLE_DROPDOWN, dropdown_name});
};

export const selectDropdown = (dropdown_name = "", selected = "") => dispatch => {
  dispatch({type: actionTypesDropdown.SELECT_DROPDOWN, dropdown_name, selected});
};

export const notifyLoadingEntities = () => dispatch => {
  dispatch({type: actionTypesEntities.NOTIFY_LOADING_ENTITIES});
};

export const setDataViewComponents = data => dispatch => {
  dispatch({type: actionTypesEntities.SET_DATA_VIEW_COMPONENTS, data});
};

export const setCurrentView = currentView => dispatch => {
  dispatch({type: actionTypesEntities.SET_CURRENT_VIEW, currentView});
};
