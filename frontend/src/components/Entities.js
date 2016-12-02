import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import Entity from './Entity';
import HowMany from './HowMany';
import Paginator from './Paginator';


class Entities extends Component {

  componentDidMount() {
    this.props.actions.getEntities(this.props.mart_id);
  }

  render() {
    const { mart_id, entities, actions } = this.props;

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
        <HowMany mart_id={mart_id} meta={meta} dropdowns={dropdowns} actions={actions}/>
        <div className={ent_class}>{render_entities}</div>
        <Paginator mart_id={mart_id} meta={meta} actions={actions}/>
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
