import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import TermsTreeItem from './TermsTreeItem';
import ActionCreators from '../actions';


function TermsTree(props) {
  const {terms, actions, termsIdsTaggedBranch} = this.props,
    term = terms.tree.root,
    {tagged, expanded, realPotential} = terms;

  if (!term)
    return null;

  return (
    <TermsTreeItem key={term.id}
                   term={term}
                   tagged={tagged}
                   expanded={expanded}
                   realPotential={realPotential}
                   actions={actions}
                   terms={terms}
                   termsIdsTaggedBranch={termsIdsTaggedBranch}/>
  );
}

const mapStateToProps = state => ({
  terms: state.terms,
});

const mapDispatchToProps = dispatch => ({
  actions: bindActionCreators(ActionCreators, dispatch),
});

export default connect(mapStateToProps, mapDispatchToProps)(TermsTree);
