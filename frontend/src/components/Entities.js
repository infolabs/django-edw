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

  componentWillReceiveProps(nextProps) {
    const req_curr = this.props.terms.tagged,
          req_next = nextProps.terms.tagged;
    if (req_curr != req_next) {
      this.props.actions.notifyLoading();
      this.props.actions.getEntities({'terms': req_next.array});
    }
  }

  render() {
    const { terms, actions } = this.props;

    let entities = terms.entities;

    if (entities.length) {
      entities = entities.map(child => <Entity key={child.id} entity={child}/>);
    } else {
      entities = "";
    }

    return (
      <div>
        <HowMany />
        <div className="entities">{entities}</div>
        <Paginator />
      </div>
    );
  }
}

function mapState(state) {
  return {
    terms: state.terms
  };
}


function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(TermsTreeActions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(Entities);
