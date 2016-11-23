import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import Entity from './Entity';
import HowMany from './HowMany';
import Paginator from './Paginator';


class Entities extends Component {

  componentDidMount() {
    this.props.actions.getEntities();
  }

  render() {
    const { entities, actions } = this.props;

    let items = entities.items.objects || [],
        meta = entities.items.meta,
        dropdowns = entities.dropdowns || {};

    let render_entities = "";
    if (items.length) {
      render_entities = items.map((child, i) => <Entity key={i} entity={child}/>);
    }

    return (
      <div>
        <HowMany meta={meta} dropdowns={dropdowns} actions={actions}/>
        <div className="entities">{render_entities}</div>
        <Paginator meta={meta} actions={actions}/>
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
