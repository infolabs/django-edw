import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
// import cookie from 'react-cookies';
import Tile from './BaseEntities/Tile';
import parseRequestParams from '../utils/parseRequestParams';
// import cookieKey from "../utils/hashUtils";
import { getDatamartsData } from "../utils/locationHash";
import ActionCreators from "../actions";
import ParticularInitiativeTile from "./Entities/ParticularInitiativeTile";
import ParticularProblemTile from "./Entities/ParticularProblemTile";


class BaseEntities extends Component {

  state = {
    initialized: false
  };

  static getTemplates() {
    return {
      "tile": Tile,
      "particular_initiative_tile": ParticularInitiativeTile,
      "particular_problem_tile": ParticularProblemTile
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

    const parms = parseRequestParams(request_params),
          term_ids = parms.term_ids,
          subj_ids = parms.subj_ids,
          limit = parms.limit,
          options_arr = parms.options_arr;

    let request_options = this.props.entities.items.meta.request_options;

    if (limit > -1)
      request_options['limit'] = limit;

    if (term_ids.length)
      request_options['terms'] = term_ids;

    // let preferences = this.getCookiePreferences();
    // request_options = Object.assign(request_options, preferences);

    this.props.notifyLoadingEntities();

    // if there's no tree and there's an offset in the location hash, make a request
    // if (this.props.terms.tree.root.children.length <= 0) {
    //   const datamartData = getDatamartsData()[entry_point_id];
    //   if (datamartData && datamartData.offset && datamartData.offset !== request_options.offset) {
    //       request_options.offset = datamartData.offset;
    //       this.props.getEntities(
    //         entry_point_id, subj_ids, request_options, options_arr
    //       );
    //       return;
    //   }
    // }

    this.props.readEntities(
      entry_point_id, subj_ids, request_options, options_arr
    );
  }

  render() {
    const {entities, entry_points, entry_point_id} = this.props;

    const items = entities.items.objects || [],
          loading = entities.items.loading,
          descriptions = entities.descriptions,
          meta = entities.items.meta;

    // set the first available component if the requested one isn't in the list
    let component_name = entities.items.component;
    if (meta.data_mart && meta.data_mart.view_components) {
      let view_components = Object.keys(meta.data_mart.view_components);
      if (view_components.length && view_components.indexOf(component_name) < 0)
        component_name = view_components[0];
    }

    if (component_name) {
      const component = this.templates[component_name] || this.templates['tile'];
      return(React.createElement(
        component, {
          items: items,
          meta: meta,
          loading: loading,
          descriptions: descriptions,
          data_mart: entry_points[entry_point_id]
        }
      ));
    } else
      return null
  }
}


const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(BaseEntities);
