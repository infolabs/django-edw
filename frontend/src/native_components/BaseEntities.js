import React, {useEffect} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {View} from 'react-native';
import parseRequestParams from '../utils/parseRequestParams';
import ActionCreators from '../actions';
import Spinner from 'react-native-loading-spinner-overlay';
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import Default from './Detail/Default';
import {baseEntitiesStyles as styles} from '../native_styles/baseEntities';


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


const defaultProps = {
  getTemplates,
};


function BaseEntities(props) {

  const {entities, entry_points, entry_point_id} = props;

  useEffect(() => {
    const request_params = entry_points[entry_point_id].request_params || [];

    const params = parseRequestParams(request_params),
      term_ids = params.term_ids,
      subj_ids = params.subj_ids,
      limit = params.limit,
      options_arr = params.options_arr;

    let request_options = entities.items.meta.request_options;

    if (limit > -1)
      request_options.limit = limit;

    if (term_ids.length)
      request_options.terms = term_ids;

    props.notifyLoadingEntities();
    props.readEntities(entry_point_id, subj_ids, request_options, options_arr);
  }, []);


  useEffect(() => {
    setComponentName();
  }, [entities.items.meta]);


  function setComponentName() {
    const meta = entities.items.meta;

    if (!entities.viewComponents.currentView && meta.data_mart && meta.data_mart.view_components) {
      // Получаем все компоненты витрины данных
      let viewComponents = Object.keys(meta.data_mart.view_components);

      // Вычисляем список ключей компонентов, которые пересекаются c API и getTemplates
      let viewComponentsMobile = [];
      let templateIsRelated = entry_points[entry_point_id].template_name &&
        entry_points[entry_point_id].template_name === 'related';
      for (let item of viewComponents) {
        if (templateIsRelated) {
          if (item.match(/(_list$)/) && props.getTemplates().hasOwnProperty(item))
              viewComponentsMobile.push(item);
          continue;
        }
        if (props.getTemplates().hasOwnProperty(item))
          viewComponentsMobile.push(item);
      }

      if (!viewComponentsMobile.length)
        viewComponentsMobile.push('list');

      const dataViewComponent = {};
      viewComponentsMobile.map(component => {
        dataViewComponent[component] = meta.data_mart.view_components[component];
      });

      props.setDataViewComponents(dataViewComponent);

      if (viewComponentsMobile.length) {
        const componentName = viewComponentsMobile[0];
        props.setCurrentView(componentName);
      }
    }
  }

  const items = entities.items.objects || [],
    {loading, meta} = entities.items,
    loadingEntity = entities.detail.loading;

  const componentName = entities.viewComponents.currentView || null;
  const templateIsDataMart = !entry_points[entry_point_id].template_name ||
      (entry_points[entry_point_id].template_name === 'data-mart');

  if (componentName) {
    const templates = props.getTemplates();
    const component = templates[componentName];
    const {notifyLoadingEntities, getEntities, getEntity} = props;

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
  } else {
    return null;
  }
}

BaseEntities.defaultProps = defaultProps;

const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(BaseEntities);
