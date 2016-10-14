import * as types from '../constants/TermsTree';


export function getTermsTree(selected = [], tagged = []) {
  // let url = Urls['edw:data-mart-terms-tree'](1, 'json')
  // console.log(Urls)
  // console.log(Urls['edw:datamart_tree'](1, 'json'))
  // nothing!
  let url = '/edw/api/data-marts/1/terms/tree.json'
  if (selected && selected.length > 0)
    url += '?selected=' + selected.join()
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
