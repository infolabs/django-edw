import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import Scroll from 'react-scroll';
import Actions from '../actions/index';
import cookie from 'react-cookies';
import List from 'components/BaseEntities/List';
import Tile from 'components/BaseEntities/Tile';
import Map from 'components/BaseEntities/Map';
import parseRequestParams from 'utils/parseRequestParams';
import hashCode from "../utils/hashUtils";


class BaseEntities extends Component {

  state = {
    initialized: false
  };

  static getTemplates() {
    return {
      "tile": Tile,
      "list": List,
      "map": Map
    };
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
          prefix = `dm_${entry_point_id}_${hashCode(document.location.pathname)}_`;

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

    let preferences = this.getCookiePreferences();
    request_options = Object.assign(request_options, preferences);

    this.props.actions.notifyLoadingEntities();

    this.props.actions.readEntities(
      entry_point_id, subj_ids, request_options, options_arr
    );
  }

  componentDidUpdate(prevProps, prevState) {
    const { entities } = this.props;

    if (!entities.items.loading && prevProps.entities.items.loading) {
      const { initialized } = this.state;

      if (initialized) {
        const area = ReactDOM.findDOMNode(this),
              areaRect = area.getBoundingClientRect(),
              bodyRect = document.body.getBoundingClientRect(),
              areaOffsetTop = areaRect.top - bodyRect.top,
              screenHeight = window.innerHeight;

        if ((areaRect.top < 0 && areaRect.top < 0.667 * (screenHeight - areaRect.height)) || areaRect.top > screenHeight) {
          const dY = Math.min(Math.round(0.25 * screenHeight), Math.abs(areaRect.top));

          Scroll.animateScroll.scrollTo(areaOffsetTop - dY, {
            duration: 700,
            delay: 200,
            smooth: true
          });
        }
      } else {
        this.setState({initialized: true});
      }
    }
  }

  render() {
    const { entities, actions, entry_points, entry_point_id } = this.props;

    const items = entities.items.objects || [],
        loading = entities.items.loading,
        descriptions = entities.descriptions,
        meta = entities.items.meta;

    // set the first available component if the requested one isn't in the list
    let component_name = entities.items.component;
    if (meta.data_mart && meta.data_mart.view_components) {
      let view_components = Object.keys(meta.data_mart.view_components);
      if (view_components.length && view_components.indexOf(component_name) < 0) {
        component_name = view_components[0];
      }
    }

    let ret = <div></div>;
    if (component_name) {
      const component = this.templates[component_name];
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
