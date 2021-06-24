import {actionTypes as actionTypesTerms} from "../constants/TermsTree";
import reCache from '../utils/reCache';
import Singleton from '../utils/singleton'

/*
Функция для получения дерева терминов
:param type: Тип вызванного действия
:param mart_id: Id витрины данных
:param selected: Массив выбранных терминов
*/
const getTermsTree = (type, mart_id, selected = []) => dispatch => {
  const instance = Singleton.getInstance(),
        {Urls, Domain} = instance;

  let url = reCache(`${Domain}${Urls['edw:data-mart-term-tree'](mart_id, 'json')}`);

  if (selected && selected.length > 0)
    url += '&selected=' + selected.join();

  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => {
    if (!instance.initial_trees || (instance.initial_trees && !Object.keys(instance.initial_trees[mart_id])).length) {
      instance['initial_trees'] = {
        [mart_id]: json
      };
    }
    dispatch({type: type, json: json})
  });
};

export const loadTree = (mart_id, selected = [])  => {
  return getTermsTree(LOAD_TERMS_TREE, mart_id, selected);
};

export const reloadTree = (mart_id, selected = []) => {
  return getTermsTree(RELOAD_TERMS_TREE, mart_id, selected);
};

export const readTree = (mart_id, selected = []) => {
  const type = actionTypesTerms.LOAD_TERMS_TREE;
  const instance = Singleton.getInstance();
  if (instance.initial_trees && instance.initial_trees[mart_id]) {
    const json = instance.initial_trees[mart_id];
    return dispatch => (
      dispatch({type, json})
    );
  } else
    return getTermsTree(type, mart_id, selected);
};

export const setPrevTaggedItems = () => dispatch => {
  dispatch({type: actionTypesTerms.SET_PREV_TAGGED_ITEMS})
};
