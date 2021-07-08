import React from 'react';
import {Provider} from 'react-redux';
import DataMart from './BaseRoot/DataMart';
import Related from './BaseRoot/Related';
import configureStore from '../store/configureStore';


export function getTemplates() {
  return {
    'data_mart': DataMart,
    'related': Related,
  };
}


function BaseRoot(props) {
  const store = configureStore();
  const {entry_points, entry_point_id} = props.attrs;
  const templates = getTemplates();

  const template_name = entry_points[entry_point_id].template_name,
      component = templates[template_name] || templates.related;

  const container_render = React.createElement(
    component, {
      entry_points: entry_points,
      entry_point_id: entry_point_id,
    }
  );

  return (
    <Provider store={store}>
      {container_render}
    </Provider>
  );
}


export default BaseRoot;
