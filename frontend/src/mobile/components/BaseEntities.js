import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import {View} from 'react-native'
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import parseRequestParams from '../utils/parseRequestParams';
import ActionCreators from "../actions";
import ParticularInitiativeTile from "./Entities/ParticularInitiativeTile";
import ParticularInitiativeList from "./Entities/ParticularInitiativeList";
import ParticularProblemTile from "./Entities/ParticularProblemTile";
import ParticularProblemList from "./Entities/ParticularProblemList";
import Spinner from 'react-native-loading-spinner-overlay';
import {baseEntitiesStyles as styles} from "../styles/baseEntities";


class BaseEntities extends Component {

  constructor() {
    super();
    this.state = {
      initialized: false
    };
  }

  static getTemplates() {
    return {
      "tile": Tile,
      "list": List,
      "particular_initiative_tile": ParticularInitiativeTile,
      "particular_initiative_list": ParticularInitiativeList,
      "particular_problem_tile": ParticularProblemTile,
      "particular_problem_list": ParticularProblemList
    };
  }

  static defaultProps = {
    getTemplates: BaseEntities.getTemplates
  };

  componentDidMount() {
    this.templates = this.props.getTemplates();

    const { entry_points, entry_point_id } = this.props,
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

    this.props.readEntities(
      entry_point_id, subj_ids, request_options, options_arr
    );

    this.setComponentName();
  }

  componentDidUpdate() {
    this.setComponentName();
  }

  setComponentName(){
    const {entities} = this.props,
          meta = entities.items.meta;

    if (!entities.viewComponents.currentView && meta.data_mart && meta.data_mart.view_components) {
      // Получаем все компоненты витрины данных
      let viewComponents = Object.keys(meta.data_mart.view_components);

      // Вычисляем список ключей компонентов, которые пересекаются c API и getTemplates
      let viewComponentsMobile = [];
      viewComponents.map(item => {
        if (this.props.getTemplates().hasOwnProperty(item))
          viewComponentsMobile.push(item)
      });

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
    const {entities, entry_points, entry_point_id} = this.props;

    const items = entities.items.objects || [],
      {loading, meta} = entities.items;

    const componentName = entities.viewComponents.currentView || null;

    if (componentName) {
      if (!this.templates)
        this.templates = this.props.getTemplates();

      const component = this.templates[componentName] || this.templates['list'];
      return(React.createElement(
        component, {
          items,
          meta,
          loading,
          entry_point_id,
          notifyLoadingEntities: this.props.notifyLoadingEntities,
          getEntities: this.props.getEntities
        }
      ));
    } else {
      return (
        <View style={styles.spinnerContainer}>
          <Spinner visible={true}/>
        </View>
      )
    }
  }
}


const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(BaseEntities);
