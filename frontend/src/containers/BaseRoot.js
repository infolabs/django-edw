import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';

import DataMart from 'containers/BaseRoot/DataMart';
import Related from 'containers/BaseRoot/Related';


export default class BaseRoot extends Component {

  get_templates () {
    return {
      "data_mart": DataMart,
      "related": Related
    }
  }

  render() {
    const { store, dom_attrs } = this.props,
          template_name_attr = dom_attrs.getNamedItem('data-template-name'),
          template_name = template_name_attr && template_name_attr.value || 'data_mart',
          component = this.get_templates()[template_name],
          mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value,
          container_render = React.createElement(
            component,
            { dom_attrs: dom_attrs,
              mart_id: mart_id }
          );

    return (
      <Provider store={store}>
        {container_render}
      </Provider>
    );
  }

}

