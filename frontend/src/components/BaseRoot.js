import React, { Component } from 'react';
import { Provider, connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index'
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

    const {store, dom_attrs, actions, datamart_list} = this.props,
      entry_points = JSON.parse(dom_attrs.getNamedItem('data-entry-points').value),
      entry_point_id_attr = dom_attrs.getNamedItem('data-selected-entry-point-id');

    let entry_point_id;

    if (datamart_list.active_mart_id) {
      entry_point_id = datamart_list.active_mart_id;
    } else if (entry_point_id_attr) {
      entry_point_id = entry_point_id_attr.value;
    } else {
      for(var key in entry_points) {
        entry_point_id = parseInt(key);
        if (!isNaN(entry_point_id)) break;
      }
    }

    const template_name = entry_points[entry_point_id].template_name || 'data_mart',
          component = this.templates[template_name];

    const container_render = React.createElement(
      component, {
        entry_points: entry_points,
        entry_point_id: entry_point_id,
        actions: actions
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
    datamart_list: state.datamart_list
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(BaseRoot);
