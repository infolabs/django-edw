import React, {Component} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import TermsTreeItem from './TermsTreeItem';
import ActionCreators from "../actions";


class TermsTree extends Component {

  render() {
    const {terms, actions} = this.props,
          term = terms.tree.root,
          details = terms.details,
          tagged = terms.tagged,
          expanded = terms.expanded,
          info_expanded = terms.info_expanded,
          loading = terms.tree.loading,
          real_potential = terms.real_potential;

    return term ? (
      <TermsTreeItem key={term.id}
                     term={term}
                     details={details}
                     tagged={tagged}
                     expanded={expanded}
                     info_expanded={info_expanded}
                     real_potential={real_potential}
                     actions={actions}/>
      )
      : null
  }
}



const mapStateToProps = state => ({
  terms: state.terms
});

const mapDispatchToProps = dispatch => {
  return {
    actions: bindActionCreators(ActionCreators, dispatch),
    dispatch: dispatch
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(TermsTree);
