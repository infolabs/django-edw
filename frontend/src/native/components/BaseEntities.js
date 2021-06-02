import React, {useMemo} from 'react';
import {View} from 'react-native';
import Spinner from 'react-native-loading-spinner-overlay';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import ActionCreators from '../actions';
import {baseEntitiesStyles as styles} from '../styles/baseEntities';
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import Default from './Detail/Default';


export function getTemplates() {
  return {
    tile: Tile,
    list: List,
  };
}


export function getTemplatesDetail() {
  return {
    default: Default,
  };
}


function BaseEntities(props) {
  const templates = useMemo(() => getTemplates(), []);

  const {entities, entry_points, entry_point_id, notifyLoadingEntities,
         getEntities, getEntity} = this.props;

  const items = entities.items.objects || [],
    {loading, meta} = entities.items,
    loadingEntity = entities.detail.loading;

  const componentName = entities.viewComponents.currentView || null;
  const templateIsDataMart = !entry_points[entry_point_id].template_name ||
      (entry_points[entry_point_id].template_name === 'data-mart');

  if (componentName) {
    const component = templates[componentName] || templates.list;
    return (React.createElement(
      component, {
        items,
        meta,
        loading,
        loadingEntity,
        entry_point_id,
        notifyLoadingEntities,
        getEntities,
        templateIsDataMart,
        getEntity,
      }
    ));
  } else if (templateIsDataMart) {
    return (
      <View style={styles.spinnerContainer}>
        <Spinner visible={true}/>
      </View>
    );
  } else
    return null;
}


const mapStateToProps = state => ({
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(BaseEntities);
