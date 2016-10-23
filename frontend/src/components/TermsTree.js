import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import _ from 'underscore';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import TermsTreeItem from './TermsTreeItem';


class TermsTree extends Component {
  componentDidMount() {
    this.props.actions.getTermsTree();
  }

  render() {
    const { terms, actions } = this.props,
          term = terms.tree.root;

    let tree = "";
    if (!_.isUndefined(term))
      tree = <TermsTreeItem key={term.id} term={term} actions={actions}/>;

    return (
      <div className="terms-tree-container">
        <ul className="terms-tree">
          {tree}
        </ul>
      </div>
    )
  }
}


function mapState(state) {
  return {
    terms: state.terms,
  };
}


function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(TermsTreeActions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(TermsTree);

