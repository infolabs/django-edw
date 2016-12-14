import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';


const templates = require('../components/templates/container').default();

import Entities from '../components/Entities';
import TermsTree from '../components/TermsTree';
import Paginator from '../components/Paginator';
import ViewComponents from '../components/ViewComponents';
import Ordering from '../components/Ordering';
import Limits from '../components/Limits';
import Statistics from '../components/Statistics';


export default class Root extends Component {

  render() {
    const { store, dom_attrs } = this.props,
          template_name_attr = dom_attrs.getNamedItem('data-template-name'),
          template_name = template_name_attr && template_name_attr.value || 'rubricator',
          component = templates[template_name],
          mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value,
          components = {
            'Entities': Entities,
            'TermsTree': TermsTree,
            'Paginator': Paginator,
            'ViewComponents': ViewComponents,
            'Ordering': Ordering,
            'Limits': Limits,
            'Statistics': Statistics
          },
          container_render = React.createElement(
            component, 
            { dom_attrs: dom_attrs,
              components: components,
              mart_id: mart_id }
          );

    return (
      <Provider store={store}>
        {container_render}
      </Provider>
    );
  }

}

