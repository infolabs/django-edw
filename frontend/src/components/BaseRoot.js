import React, { Component } from 'react';
import { Provider } from 'react-redux';

import DataMart from 'components/BaseRoot/DataMart';
import Related from 'components/BaseRoot/Related';



class BaseRoot extends Component {

  static getTemplates() {
    return {
      "data_mart": DataMart,
      "related": Related
    }
  }

  static defaultProps = {
    getTemplates: BaseRoot.getTemplates
  };

  componentWillMount() {
    this.templates = this.props.getTemplates();
  }

  render() {
    const {store, dom_attrs} = this.props,
          template_name_attr = dom_attrs.getNamedItem('data-template-name'),
          template_name = template_name_attr && template_name_attr.value || 'data_mart',
          component = this.templates[template_name],
          mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value,
          container_render = React.createElement(
            component, {
              dom_attrs: dom_attrs,
              mart_id: mart_id
            }
          );

    return (
      <Provider store={store}>
        {container_render}
      </Provider>
    );
  }

}

export default BaseRoot;
