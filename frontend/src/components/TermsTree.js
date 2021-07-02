import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../actions/index';
import TermsTreeItem from './TermsTreeItem';
import parseRequestParams from 'utils/parseRequestParams';
import { setDatamartHash, getDatamartsData } from '../utils/locationHash';


function isArraysEqual(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length !== b.length) return false;

  for (let i = 0; i < a.length; ++i) {
    if (a[i] !== b[i])
      return false;
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

    this.props.actions.notifyLoadingTerms();
    this.props.actions.readTree(entry_point_id, term_ids);
  }

  componentDidUpdate(prevProps) {
    const entry_points = prevProps.entry_points,
          entry_point_id = prevProps.entry_point_id,
          request_params = entry_points[entry_point_id.toString()].request_params || [],
          tagged_current = prevProps.terms.tagged,
          tagged_next = this.props.terms.tagged,
          meta = prevProps.entities.items.meta;

    const parms = parseRequestParams(request_params),
          subj_req_ids = parms.subj_ids,
          options_arr = parms.options_arr;

    let request_options = meta.request_options,
        subj_ids = meta.subj_ids || subj_req_ids;


    if (!isArraysEqual(tagged_current.items, tagged_next.items)) {
      // get from hash if exist
      const datamartData = getDatamartsData()[entry_point_id];
      const fromHash = !tagged_current.items.length && datamartData && datamartData.terms && datamartData.terms.length;
      if (fromHash)
        tagged_next.items = datamartData.terms;

      if (tagged_current.items.length)
        setDatamartHash(entry_point_id, tagged_next.items, request_options.offset);

      // reload tree
      if (!tagged_next.isInCache() || fromHash) {
        this.props.actions.notifyLoadingTerms();
        const func = fromHash ? this.props.actions.loadTree : this.props.actions.reloadTree;
        func(entry_point_id, tagged_next.items);
      }
      // reload entities
      if (!tagged_next.entities_ignore || fromHash) {
        delete request_options.alike;
        request_options.terms = tagged_next.items;
        request_options.offset = fromHash ? datamartData.offset : 0;
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
          infoExpanded = terms.infoExpanded,
          loading = terms.tree.loading,
          realPotential = terms.realPotential;

    let tree = '';
    if (term) {
      tree = (
        <TermsTreeItem key={term.id}
                       term={term}
                       details={details}
                       tagged={tagged}
                       expanded={expanded}
                       infoExpanded={infoExpanded}
                       realPotential={realPotential}
                       actions={actions}/>
      );
    }

    let ul_class = loading ? 'terms-tree ex-state-loading' : 'terms-tree';

    return (
        <ul className={ul_class}>
          {tree}
        </ul>
    );
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
    dispatch: dispatch,
  };
}


export default connect(mapState, mapDispatch)(TermsTree);
