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
      this.props.actions.getEntities({'terms': req_next.array, 'limit': 1});
    }
  }

  render() {
    const { terms, actions } = this.props;

    let entities = terms.entities.objects || [],
        meta = terms.entities.meta;

    if (entities.length) {
      entities = entities.map((child, i) => <Entity key={i} entity={child}/>);
    } else {
      entities = "";
    }

    return (
      <div>
        <HowMany />
        <div className="entities">{entities}</div>
        <Paginator meta={meta} actions={actions}/>
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
