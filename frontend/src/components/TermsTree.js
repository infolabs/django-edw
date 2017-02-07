import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import * as TermsTreeActions from '../actions/TermsTreeActions';
import TermsTreeItem from './TermsTreeItem';


function isArraysEqual(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length != b.length) return false;

  for (let i = 0; i < a.length; ++i) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}


class TermsTree extends Component {

  componentDidMount() {
    const dom_attrs = this.props.dom_attrs,
          mart_id = this.props.mart_id,
          terms_attr = dom_attrs.getNamedItem('data-terms');

    let term_ids = [];
    if (terms_attr && terms_attr.value)
      term_ids = terms_attr.value.split(",");

    this.props.actions.notifyLoading();
    this.props.actions.loadTree(mart_id, term_ids);
  }

  componentWillReceiveProps(nextProps) {
    const dom_attrs = this.props.dom_attrs,
          mart_id = this.props.mart_id,
          subj_attr = dom_attrs.getNamedItem('data-subj'),
          tagged_current = this.props.terms.tagged,
          tagged_next = nextProps.terms.tagged,
          meta = this.props.entities.items.meta;

    if (!isArraysEqual(tagged_current.items, tagged_next.items)) {
      // reload tree
      if (!tagged_next.isInCache()) {
        this.props.actions.notifyLoading();
        this.props.actions.reloadTree(mart_id, tagged_next.items);
      }

      // reload entities
      let request_options = meta.request_options,
          subj_ids = meta.subj_ids;

      if (!subj_ids && subj_attr && subj_attr.value)
        subj_ids = subj_attr.value.split(",");

      request_options['terms'] = tagged_next.items;
      request_options['offset'] = 0;
      this.props.actions.notifyLoadingEntities();
      this.props.actions.getEntities(mart_id, subj_ids, request_options);
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
    entities: state.entities,
  };
}


function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(TermsTreeActions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(TermsTree);

