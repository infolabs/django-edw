import * as types from '../constants/RubricatorActionTypes';

export function getTermsTree(tagged_ids = []) {
  // todo: мы используем
  // <script src="{% url 'js_reverse' %}" type="text/javascript"></script>
  //   https://github.com/ierror/django-js-reverse#overview
  // поэтому из урла
  // ^edw/ ^api/ ^ ^data-marts/(?P<data_mart_pk>[^/.]+)/terms/tree\.(?P<format>[a-z0-9]+)/?$ [name='data-mart-terms-tree']
  // получаем
  // let url = Urls['edw:data-mart-terms-tree'](1, 'json')
  let url = '/edw/api/data-marts/1/terms/tree.json'
  // let url = '/edw/api/data-marts/1/terms/tree/?format=json'
  if (tagged_ids && tagged_ids.length > 0)
    url = '/edw/api/data-marts/1/terms/tree.json?selected=' + tagged_ids.join() // todo: может url += '?selected='...
    // url = '/edw/api/data-marts/1/terms/tree/?selected=' + tagged_ids.join() + '&format=json'

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
