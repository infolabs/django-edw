import React, {Component} from 'react'
import {Provider} from 'react-redux'
import DataMart from './BaseRoot/DataMart'
import Related from './BaseRoot/Related'
import configureStore from "../store/configureStore"
import Singleton from "../utils/singleton";


class BaseRoot extends Component {

  static getTemplates() {
    return {
      "data_mart": DataMart,
      "related": Related
    };
  }

  static defaultProps = {
    getTemplates: BaseRoot.getTemplates
  };

  constructor(props) {
    super(props);
    this.templates = this.props.getTemplates();
  }

  render() {
    const instance = Singleton.getInstance();

    const {attrs} = this.props,
          store = configureStore(),
          {entry_points, entry_point_id} = attrs;

    const template_name = entry_points[entry_point_id].template_name,
          component = this.templates[template_name] || this.templates['data_mart'];

    const container_render = React.createElement(
      component, {
        entry_points: entry_points,
        entry_point_id: entry_point_id
      }
    );

    return(
      <Provider store={store}>
        {container_render}
      </Provider>
    )
  }
}

export default BaseRoot;
