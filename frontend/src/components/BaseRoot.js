import React, { Component } from 'react';
import { Provider, connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index';
import DataMart from 'components/BaseRoot/DataMart';
import Related from 'components/BaseRoot/Related';


class BaseRoot extends Component {

  static getTemplates() {
    return {
      'data_mart': DataMart,
      'related': Related,
    };
  }

  static defaultProps = {
    getTemplates: BaseRoot.getTemplates,
  };

  constructor(props) {
    super(props);
    this.templates = this.props.getTemplates();
  }

  render() {

    const {store, dom_attrs, actions, datamart_list} = this.props,
          entry_points_item = dom_attrs.getNamedItem('data-entry-points'),
          entry_points = entry_points_item
            ? JSON.parse(dom_attrs.getNamedItem('data-entry-points').value) : {},
          entry_point_id_attr = dom_attrs.getNamedItem('data-selected-entry-point-id');
    let component_attrs = dom_attrs.getNamedItem('data-component-attrs') || {};

    if (Object.keys(entry_points).length === 0 && entry_point_id_attr)
      entry_points[entry_point_id_attr.value] = {};

    if (component_attrs.value)
      component_attrs = JSON.parse(component_attrs.value);

    let entry_point_id;

    if (datamart_list.active_mart_id) {
      entry_point_id = datamart_list.active_mart_id;
    } else if (entry_point_id_attr) {
      entry_point_id = entry_point_id_attr.value;
    } else {
      for (var key in entry_points) {
        entry_point_id = parseInt(key, 10);
        if (!isNaN(entry_point_id)) break;
      }
    }

    const template_name = entry_points[entry_point_id].template_name || 'data_mart',
          component = this.templates[template_name];

    const container_render = React.createElement(
      component, {
        entry_points: entry_points,
        entry_point_id: entry_point_id,
        actions: actions,
        component_attrs: component_attrs,
      }
    );

    return (
      <Provider store={store}>
        {container_render}
      </Provider>
    );
  }

}


function mapState(state) {
  return {
    datamart_list: state.datamart_list,
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch,
  };
}


export default connect(mapState, mapDispatch)(BaseRoot);
