import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import {
    getTermsItem,
    loadTree,
    reloadTree,
    notifyLoading,
    toggle,
    resetItem,
    resetBranch,
    showInfo,
    hideInfo
} from '../actions/TermsTreeActions';
import {
    getEntityItem,
    getEntities,
    notifyLoadingEntities,
    showDescription,
    hideDescription,
    toggleDropdown,
    selectDropdown
} from '../actions/EntityActions';
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

  componentDidMount() {
    const dom_attrs = this.props.dom_attrs,
          mart_attr = dom_attrs.getNamedItem('data-data-mart-pk'),
          subj_attr = dom_attrs.getNamedItem('data-subj'),
          terms_attr = dom_attrs.getNamedItem('data-terms');

    let subj_ids = [];
    if (subj_attr && subj_attr.value)
      subj_ids = subj_attr.value.split(",");

    let term_ids = [];
    if (terms_attr && terms_attr.value)
      term_ids = terms_attr.value.split(",");

    this.props.actions.notifyLoadingEntities();
    this.props.actions.getEntities(
      mart_attr.value, subj_ids, {'terms': term_ids}
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
    actions: bindActionCreators({
        getTermsItem,
        loadTree,
        reloadTree,
        notifyLoading,
        toggle,
        resetItem,
        resetBranch,
        showInfo,
        hideInfo,
        getEntityItem,
        getEntities,
        notifyLoadingEntities,
        showDescription,
        hideDescription,
        toggleDropdown,
        selectDropdown
    }, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(BaseEntities);
