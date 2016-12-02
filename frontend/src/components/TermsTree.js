import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import TermsTreeItem from './TermsTreeItem';


class TermsTree extends Component {
  componentDidMount() {
    this.props.actions.loadTree(this.props.mart_id);
  }

  componentWillReceiveProps(nextProps) {
    // Reload tree on new requested term
    const req_curr = this.props.terms.tagged,
          req_next = nextProps.terms.tagged;
    if (req_curr != req_next) {
      this.props.actions.notifyLoading();
      this.props.actions.reloadTree(this.props.mart_id, req_next.array);
    }

    // Reload entires on toggled term
    const tag_curr = this.props.terms.tagged,
          tag_next = nextProps.terms.tagged;
    if (tag_curr != tag_next) {
      this.props.actions.notifyLoadingEntities();
      this.props.actions.getEntities(this.props.mart_id, {'terms': tag_next.array});
    }
  }

  render() {
    const { terms, actions } = this.props,
          term = terms.tree.root,
          details = terms.details,
          tagged = terms.tagged,
          expanded = terms.expanded,
          info_expanded = terms.info_expanded,
          loading = terms.tree.loading,
          real_potential = terms.real_potential;

    let tree = "";
    if ( !!term ) {
      tree = (
        <TermsTreeItem key={term.id}
                       term={term}
                       details={details}
                       tagged={tagged}
                       expanded={expanded}
                       info_expanded={info_expanded}
                       real_potential={real_potential}
                       actions={actions}/>
      );
    }

    let ul_class = loading ? "terms-tree ex-state-loading" : "terms-tree";

    return (
        <ul className={ul_class}>
          {tree}
        </ul>
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

