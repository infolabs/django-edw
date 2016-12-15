import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from 'actions/TermsTreeActions';

import List from 'components/templates/entity/List';
import Tile from 'components/templates/entity/Tile';


class BaseEntities extends Component {

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

  get_templates() {
    return {
        "tile": Tile,
        "list": List
    };
  }

  render() {
    const { dom_attrs, entities, actions, mart_id } = this.props;

    const items = entities.items.objects || [],
        meta = entities.items.meta,
        dropdowns = entities.dropdowns || {},
        loading = entities.items.loading,
        descriptions = entities.descriptions;

    const ent_class = loading ? "entities ex-state-loading" : "entities";

    let ret = <div></div>;
    if (entities.items && entities.items.component) {
      const templates = this.get_templates();

      console.log("*****", templates);

      const component = templates[entities.items.component];
      ret = React.createElement(
        component, {items: items,
                    actions: actions,
                    descriptions: descriptions}
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
    actions: bindActionCreators(TermsTreeActions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(BaseEntities);
