import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import React, {Component} from 'react';
import {View} from 'react-native'
import parseRequestParams from '../utils/parseRequestParams';
import ActionCreators from "../actions";
import Spinner from 'react-native-loading-spinner-overlay';
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import Default from './Detail/Default';
import {baseEntitiesStyles as styles} from "../styles/baseEntities";


class BaseEntities extends Component {

  static getTemplates() {
    return {
      "tile": Tile,
      "list": List,
    };
  }

  static getTemplatesDetail() {
    return {
      "default": Default,
    }
  }

  static defaultProps = {
    getTemplates: BaseEntities.getTemplates
  };

  componentDidMount() {
    this.templates = this.props.getTemplates();

    const {entry_points, entry_point_id} = this.props,
      request_params = entry_points[entry_point_id].request_params || [];

    const params = parseRequestParams(request_params),
      term_ids = params.term_ids,
      subj_ids = params.subj_ids,
      limit = params.limit,
      options_arr = params.options_arr;

    let request_options = this.props.entities.items.meta.request_options;

    if (limit > -1)
      request_options['limit'] = limit;

    if (term_ids.length)
      request_options['terms'] = term_ids;

    this.props.notifyLoadingEntities();
    this.props.readEntities(entry_point_id, subj_ids, request_options, options_arr);
    this.setComponentName();
  }

  componentDidUpdate() {
    this.setComponentName();
  }

  setComponentName() {
    const {entities, entry_points, entry_point_id} = this.props,
      meta = entities.items.meta;

    if (!entities.viewComponents.currentView && meta.data_mart && meta.data_mart.view_components) {
      // Получаем все компоненты витрины данных
      let viewComponents = Object.keys(meta.data_mart.view_components);

      // Вычисляем список ключей компонентов, которые пересекаются c API и getTemplates
      let viewComponentsMobile = [];
      let templateIsRelated = entry_points[entry_point_id].template_name &&
        entry_points[entry_point_id].template_name === 'related';
      for (let item of viewComponents) {
        if (templateIsRelated) {
          if (item.match(/(_list$)/))
            if (this.props.getTemplates().hasOwnProperty(item))
              viewComponentsMobile.push(item);
          continue;
        }
        if (this.props.getTemplates().hasOwnProperty(item))
          viewComponentsMobile.push(item)
      }

      if (templateIsRelated && !viewComponentsMobile.length)
        viewComponentsMobile.push('list');

      const dataViewComponent = {};
      viewComponentsMobile.map(component => {
        dataViewComponent[component] = meta.data_mart.view_components[component]
      });

      this.props.setDataViewComponents(dataViewComponent);

      if (viewComponentsMobile.length) {
        const componentName = viewComponentsMobile[0];
        this.props.setCurrentView(componentName)
      }
    }
  }

  render() {
    const {entities, entry_points, entry_point_id, notifyLoadingEntities, getEntities, getEntity} = this.props;

    const items = entities.items.objects || [],
      {loading, meta} = entities.items,
      loadingEntity = entities.detail.loading;

    const componentName = entities.viewComponents.currentView || null;
    const templateIsDataMart = !entry_points[entry_point_id].template_name ||
        (entry_points[entry_point_id].template_name === 'data-mart');

    if (componentName) {
      if (!this.templates)
        this.templates = this.props.getTemplates();

      const component = this.templates[componentName] || this.templates['list'];
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
          getEntity
        }
      ));
    } else if (templateIsDataMart) {
      return (
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
      )
    } else {
      return null
    }
  }
}


const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(BaseEntities);
