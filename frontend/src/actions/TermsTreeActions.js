import * as types from '../constants/TermsTree';


export function getTermsTree(selected = [], tagged = []) {

  // edw/api/data-marts/1/terms/tree.json
  // console.log(Urls['edw:term\u002Dtree']('json') + "?data_mart_pk=1");

  let url = Urls['edw:term\u002Dtree']('json') + "?data_mart_pk=1"

  if (selected && selected.length > 0)
    url += '&selected=' + selected.join()
  return fetch(url, {
    method: 'get',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
  }).then(response => response.json()).then(json => ({
    type: types.GET_TERMS_TREE,
    json: json,
    selected: selected,
    tagged: tagged,
  }));
}


export function toggle(term = {}) {
  return {
    type: types.TOGGLE,
    term: term,
  };
}

export function resetItem(term = {}) {
  return {
    type: types.RESET_ITEM,
    term: term,
  };
}
