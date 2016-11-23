import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import TermsTreeItem from './TermsTreeItem';


class TermsTree extends Component {
  componentDidMount() {
    this.props.actions.loadTree();
  }

  componentWillReceiveProps(nextProps) {
    // Reload tree on new requested term
    const req_curr = this.props.terms.requested,
          req_next = nextProps.terms.requested;
    if (req_curr != req_next) {
      this.props.actions.notifyLoading();
      this.props.actions.reloadTree(req_next.array);
    }

    // Reload entires on toggled term
    const tag_curr = this.props.terms.tagged,
          tag_next = nextProps.terms.tagged;
    if (tag_curr != tag_next) {
      this.props.actions.notifyLoading();
      this.props.actions.getEntities({'terms': tag_next.array});
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
    return (
        <ul className="terms-tree">
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

