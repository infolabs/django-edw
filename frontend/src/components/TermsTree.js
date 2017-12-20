import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../actions/index'
import TermsTreeItem from './TermsTreeItem';
import parseRequestParams from 'utils/parseRequestParams';


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
    const entry_points = this.props.entry_points,
          entry_point_id = this.props.entry_point_id,
          request_params = entry_points[entry_point_id.toString()].request_params || [];

    const parms = parseRequestParams(request_params),
          term_ids = parms.term_ids;

    this.props.actions.notifyLoading();
    this.props.actions.loadTree(entry_point_id, term_ids);
  }

  componentWillReceiveProps(nextProps) {
    const entry_points = this.props.entry_points,
          entry_point_id = this.props.entry_point_id,
          request_params = entry_points[entry_point_id.toString()].request_params || [],
          tagged_current = this.props.terms.tagged,
          tagged_next = nextProps.terms.tagged,
          meta = this.props.entities.items.meta;

    if (!isArraysEqual(tagged_current.items, tagged_next.items)) {
      // reload tree
      if (!tagged_next.isInCache()) {
        this.props.actions.notifyLoading();
        this.props.actions.reloadTree(entry_point_id, tagged_next.items);
      }

      // reload entities
      if (!tagged_next.entities_ignore) {
        const parms = parseRequestParams(request_params),
              subj_req_ids = parms.subj_ids,
              options_arr = parms.options_arr;

        let request_options = meta.request_options,
            subj_ids = meta.subj_ids || subj_req_ids;

        request_options['terms'] = tagged_next.items;
        request_options['offset'] = 0;
        this.props.actions.notifyLoadingEntities();

        this.props.actions.getEntities(
          entry_point_id, subj_ids, request_options, options_arr
        );

      }
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
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(TermsTree);

