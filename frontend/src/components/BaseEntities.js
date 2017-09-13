import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../actions/index'
import cookie from 'react-cookies'
import List from 'components/BaseEntities/List';
import Tile from 'components/BaseEntities/Tile';
import Map from 'components/BaseEntities/Map';

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
    const dom_attrs = this.props.dom_attrs,
          mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value;
    const cookie_data = cookie.loadAll();
    const prefix = "datamart_prefs_" + mart_id + "_";
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
    const dom_attrs = this.props.dom_attrs,
          mart_attr = dom_attrs.getNamedItem('data-data-mart-pk'),
          subj_attr = dom_attrs.getNamedItem('data-subj'),
          terms_attr = dom_attrs.getNamedItem('data-terms');

    let request_options = this.props.entities.items.meta.request_options;

    let subj_ids = [];
    if (subj_attr && subj_attr.value)
      subj_ids = subj_attr.value.split(",");

    let term_ids = [];
    if (terms_attr && terms_attr.value)
      term_ids = terms_attr.value.split(",");

    request_options['terms'] = term_ids;
    const preferences = this.getCookiePreferences();
    request_options = Object.assign(request_options, preferences);

    this.props.actions.notifyLoadingEntities();

    this.props.actions.getEntities(
      mart_attr.value, subj_ids, request_options
    );
  }

  render() {
    const { entities, actions } = this.props;

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
          descriptions: descriptions
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
