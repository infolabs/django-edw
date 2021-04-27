import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import {View, StyleSheet} from 'react-native'
// import cookie from 'react-cookies';
import Tile from './BaseEntities/Tile';
import List from './BaseEntities/List';
import parseRequestParams from '../utils/parseRequestParams';
// import cookieKey from "../utils/hashUtils";
import ActionCreators from "../actions";
import ParticularInitiativeTile from "./Entities/ParticularInitiativeTile";
import ParticularInitiativeList from "./Entities/ParticularInitiativeList";
import ParticularProblemTile from "./Entities/ParticularProblemTile";
import ParticularProblemList from "./Entities/ParticularProblemList";
import Spinner from 'react-native-loading-spinner-overlay';
import platformSettings from "../constants/Platform";


class BaseEntities extends Component {

  constructor() {
    super();
    this.state = {
      initialized: false,
      componentName: null
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

  // getCookiePreferences() {
  //   const entry_point_id = this.props.entry_point_id,
  //         cookie_data = cookie.loadAll(),
  //         prefix = cookieKey(entry_point_id, document.location.pathname, '');
  //
  //   let preferences = {};
  //
  //   for (const k of Object.keys(cookie_data)) {
  //     if (k.startsWith(prefix)) {
  //       const meta_key = k.slice(prefix.length);
  //       preferences[meta_key] = decodeURI(cookie_data[k]);
  //     }
  //   }
  //
  //   return preferences;
  // }

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

    // let preferences = this.getCookiePreferences();
    // request_options = Object.assign(request_options, preferences);

    this.props.notifyLoadingEntities();

    this.props.readEntities(
      entry_point_id, subj_ids, request_options, options_arr
    );

    this.setComponentName();
  }

  componentDidUpdate() {
    this.setComponentName();
    const currentView = this.props.entities.viewComponents.currentView;
    if (this.state.componentName !== currentView) {
      this.setState({
        componentName: currentView
      })
    }
  }

  setComponentName(){
    const {entities} = this.props,
          meta = entities.items.meta;

    if (!this.state.componentName && meta.data_mart && meta.data_mart.view_components) {
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
        this.setState({
          componentName
        });
        this.props.setCurrentView(componentName)
      }
    }
  }

  render() {
    const {entities, entry_points, entry_point_id} = this.props;

    const items = entities.items.objects || [],
          loading = entities.items.loading,
          descriptions = entities.descriptions,
          meta = entities.items.meta;

    const {deviceHeight, deviceWidth} = platformSettings;
    const styles = StyleSheet.create({
      spinnerContainer: {
        height: deviceHeight,
        width: deviceWidth,
        justifyContent: 'center',
        alignItems: 'center',
      }
    });

    if (this.state.componentName) {
      if (!this.templates)
        this.templates = this.props.getTemplates();

      const component = this.templates[this.state.componentName] || this.templates['list'];
      return(React.createElement(
        component, {
          items: items,
          meta: meta,
          loading: loading,
          descriptions: descriptions,
          data_mart: entry_points[entry_point_id]
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
