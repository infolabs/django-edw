import React, {useEffect} from 'react';
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
  // a mobile app uses its own store, in order to get the edw store
  // one can pass an event handler on store changes
  const subscribe = props.onEdwStoreChange;

  useEffect(() => {
    if (subscribe)
      store.subscribe(() => subscribe(store));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subscribe]);

  const {template_name, dataMartName} = entry_points[entry_point_id],
    component = templates[template_name] || templates.data_mart;

  const container_render = React.createElement(
    component, {
      dataMartName,
      ...props.attrs,
    }
  );

  return (
    <Provider store={store}>
      {container_render}
    </Provider>
  );
}


export default BaseRoot;
