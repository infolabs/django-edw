import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../actions/index'
import cookie from 'react-cookies'
import List from 'components/BaseEntities/List';
import Tile from 'components/BaseEntities/Tile';
import Map from 'components/BaseEntities/Map';
import parseRequestParams from 'utils/parseRequestParams';


class BaseEntities extends Component {

  static getTemplates() {
    return {
      "tile": Tile,
      "list": List,
      "map": Map
    }
  }

  static defaultProps = {
    getTemplates: BaseEntities.getTemplates
  };

  componentWillMount() {
    this.templates = this.props.getTemplates();
  }

  getCookiePreferences() {
    const entry_point_id = this.props.entry_point_id,
          cookie_data = cookie.loadAll(),
          prefix = "datamart_prefs_" + entry_point_id + "_";

    let preferences = {};

    for (const k of Object.keys(cookie_data)) {
      if (k.startsWith(prefix)) {
        const meta_key = k.slice(prefix.length);
        preferences[meta_key] = decodeURI(cookie_data[k]);
      }
    }
    return preferences;
  }

  componentDidMount() {
    const { entry_points, entry_point_id } = this.props,
          request_params = entry_points[entry_point_id].request_params || [];

    const parms = parseRequestParams(request_params),
          term_ids = parms.term_ids,
          subj_ids = parms.subj_ids,
          limit = parms.limit,
          options_arr = parms.options_arr;

    let request_options = this.props.entities.items.meta.request_options;

    if (limit > -1) {
      request_options['limit'] = limit;
    }
    if (term_ids.length) {
      request_options['terms'] = term_ids;
    }
    const preferences = this.getCookiePreferences();
    request_options = Object.assign(request_options, preferences);

    this.props.actions.notifyLoadingEntities();

    this.props.actions.getEntities(
      entry_point_id, subj_ids, request_options, options_arr
    );
  }

  render() {
    const { entities, actions, entry_points, entry_point_id } = this.props;

    const items = entities.items.objects || [],
        dropdowns = entities.dropdowns || {},
        loading = entities.items.loading,
        descriptions = entities.descriptions,
        meta = entities.items.meta;

    let ret = <div></div>;
    if (entities.items && entities.items.component) {
      const component = this.templates[entities.items.component];
      ret = React.createElement(
        component, {
          items: items,
          actions: actions,
          meta: meta,
          loading: loading,
          descriptions: descriptions,
          data_mart: entry_points[entry_point_id]
        }
      );
    }

    return ret;
  }
}


function mapState(state) {
  return {
    entities: state.entities,
  };
}


function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(BaseEntities);
