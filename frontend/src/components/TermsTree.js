import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component, PropTypes } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions'; //TermsTreeActions
import { TOGGLE } from '../constants/TermsTree';
import TermsTreeItem from './TermsTreeItem'; //TermsTreeItem

class TermsTree extends Component {

  componentDidMount() {
    this.props.actions.toggle();
  }

  componentWillReceiveProps(nextProps) {
    //subscribe fetch to props change
    if (nextProps.terms && nextProps.terms.do_request) {
      this.props.dispatch(TermsTreeActions.getTermsTree(
          nextProps.terms.terms_tree.selected,
          nextProps.terms.terms_tree.tagged
      ));
    }
  }

  render() {
    const { terms, actions } = this.props;
    let terms_tree = [];
    if (typeof terms.terms_tree !== 'undefined')
      terms_tree = terms.terms_tree.tree

    return (
    <div className="terms-tree-container">
      <ul className="terms-tree">
        {terms_tree.map(term =>
          <TermsTreeItem key={term.id} //TermsTreeItem
                          term={term}
                          actions={actions}
                          />
        )}
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

