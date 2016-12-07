import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import Entity from './Entity';
import ToolBar from './ToolBar';
import Paginator from './Paginator';


class Entities extends Component {

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
    const { dom_attrs, entities, actions } = this.props;
    const mart_id = dom_attrs.getNamedItem('data-data-mart-pk').value;

    let items = entities.items.objects || [],
        meta = entities.items.meta,
        dropdowns = entities.dropdowns || {},
        loading = entities.items.loading,
        component = entities.items.component;

    let ent_class = loading ? "entities ex-state-loading" : "entities";

    let render_entities = "";
    if (items.length) {
      render_entities = items.map((child, i) => <Entity key={i} entity={child} component={component}/>);
    }

    return (
      <div>
        <ToolBar mart_id={mart_id} meta={meta} dropdowns={dropdowns} actions={actions}/>
        <ul className={ent_class}>{render_entities}</ul>
        <div className="row">
          <Paginator mart_id={mart_id} meta={meta} actions={actions}/>
        </div>
      </div>
    );
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


export default connect(mapState, mapDispatch)(Entities);
