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
import YMap from 'components/BaseEntities/YMap';
import parseRequestParams from 'utils/parseRequestParams';
import cookieKey from "../utils/hashUtils";
import { getDatamartsData } from "../utils/locationHash";

class BaseEntities extends Component {

  state = {
    initialized: false
  };

  static getTemplates() {
    return {
      "tile": Tile,
      "list": List,
      "map": Map,
      "ymap": YMap
    };
  }

  static defaultProps = {
    getTemplates: BaseEntities.getTemplates
  };

  getCookiePreferences() {
    const entry_point_id = this.props.entry_point_id,
          cookie_data = cookie.loadAll(),
          prefix = cookieKey(entry_point_id, document.location.pathname, '');

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
    this.templates = this.props.getTemplates();

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

    // if there's no tree and there's an offset in the location hash, make a request
    if (this.props.terms.tree.root.children.length <= 0) {
      const datamartData = getDatamartsData()[entry_point_id];
      if (datamartData && datamartData.offset && datamartData.offset != request_options.offset) {
          request_options.offset = datamartData.offset;
          this.props.actions.getEntities(
            entry_point_id, subj_ids, request_options, options_arr
          );
          return;
      }
    }

    this.props.actions.readEntities(
      entry_point_id, subj_ids, request_options, options_arr
    );
  }

  componentDidUpdate(prevProps, prevState) {
    const { entities } = this.props;

    if (!entities.items.loading && prevProps.entities.items.loading) {
      const { initialized } = this.state,
            area = ReactDOM.findDOMNode(this);

      if (initialized && area) {
        const areaRect = area.getBoundingClientRect(),
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
    const { entities, actions, entry_points, entry_point_id, component_attrs } = this.props;

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
      if (!this.templates)
        this.templates = this.props.getTemplates();

      const component = this.templates[component_name];
      ret = React.createElement(
        component, {
          items: items,
          actions: actions,
          meta: meta,
          loading: loading,
          descriptions: descriptions,
          data_mart: entry_points[entry_point_id],
          component_attrs: component_attrs
        }
      );
    }

    return ret;
  }
}


function mapState(state) {
  return {
    terms: state.terms,
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
