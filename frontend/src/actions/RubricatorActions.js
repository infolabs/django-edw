import * as types from '../constants/RubricatorActionTypes';

export function getTermsTree(tagged_ids = []) {

  let url = '/edw/api/data-marts/1/terms/tree/?format=json'
  if (tagged_ids && tagged_ids.length > 0)
    url = '/edw/api/data-marts/1/terms/tree/?selected=' + tagged_ids.join() + '&format=json'

  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: types.GET_TERMS_TREE,
    json: json,
    selected: tagged_ids,
  }));
}


export function toggle(term = {}) {
  return {
    type: types.TOGGLE,
    term: term,
  };
}
