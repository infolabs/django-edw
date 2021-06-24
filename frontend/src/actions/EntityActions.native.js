import {Platform} from 'react-native';
import matchAll from 'string.prototype.matchall';
import {actionTypes as actionTypesEntities} from "../constants/Entities";
import {actionTypes as actionTypesDropdown} from "../constants/Dropdown";
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton';

import {
  opts2gets,
  optArrToObj,
} from './EntityActions.js';

const instance = Singleton.getInstance();


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


export const getEntity = (data, meta= false) => {
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
    dispatch({type: actionTypesEntities.NOTIFY_LOADING_ENTITY});
    const {detail} = getState().entities;
    if (detail.data.id !== data.id) {
      fetch(url, {
        method: 'get',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
      })
        .then(response => response.json())
        .then(json => {
          // TODO: MatchAll в react-native v0.64.2 для андроида не поддерживается. Возможно, пофиксят в будущем, и тогда
          // нужно будет убрать проверку и удалить пакет string.prototype.matchall.
          const arrayMediaEntity = Platform.OS === 'ios' ?
            Array.from(json.media.matchAll(/(?:src=['\"])(\/media\S+.[jpg|jpeg|png])/gm))
            :
            [...matchAll(json.media, /(?:src=['\"])(\/media\S+.[jpg|jpeg|png])/gm)];

          json.media = arrayMediaEntity.map(item => `${instance.Domain}${item[1]}`);

          if (json.private_person)
            json.private_person.media = `${instance.Domain}${json.private_person.media.match(/.*<img.*?src=(['"])(.*?)(['"])/)[2]}`;
          return dispatch({type: actionTypesEntities.LOAD_ENTITY, json});
        });
    } else
      dispatch({type: actionTypesEntities.DO_NOTHING})
  };
};

export const hideVisibleDetail = () => dispatch => {
  dispatch({type: actionTypesEntities.HIDE_VISIBLE_DETAIL})
};

export const setDataViewComponents = data => dispatch => {
  dispatch({type: actionTypesEntities.SET_DATA_VIEW_COMPONENTS, data});
};

export const setCurrentView = currentView => dispatch => {
  dispatch({type: actionTypesEntities.SET_CURRENT_VIEW, currentView});
};
