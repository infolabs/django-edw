import React, {Component} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import TermsTreeItem from './TermsTreeItem';
import ActionCreators from "../actions";
import parseRequestParams from "../utils/parseRequestParams"
import {isArraysEqual} from "../utils/isArrayEqual";


class TermsTree extends Component {

  componentDidMount() {
    const entry_points = this.props.entry_points,
      entry_point_id = this.props.entry_point_id,
      request_params = entry_points[entry_point_id.toString()].request_params || [];

    const params = parseRequestParams(request_params),
      term_ids = params.term_ids;

    this.props.actions.notifyLoading();
    this.props.actions.readTree(entry_point_id, term_ids);

    const tagged = this.props.terms.tagged,
      {termsIdsStructureIsLimb} = this.props.terms.tree;

    let countTaggedBranch = 0;
    tagged.items.map(item => {
      if (termsIdsStructureIsLimb.includes(item))
        countTaggedBranch++;
    });
    this.props.actions.setCountTaggedBranch(countTaggedBranch);
  }

  componentDidUpdate(prevProps) {
    const entry_points = prevProps.entry_points,
      entry_point_id = prevProps.entry_point_id,
      request_params = entry_points[entry_point_id.toString()].request_params || [],
      tagged_current = prevProps.terms.tagged,
      tagged_next = this.props.terms.tagged,
      {termsIdsStructureIsLimb} = this.props.terms.tree,
      meta = prevProps.entities.items.meta;

    if (!isArraysEqual(tagged_current.items, tagged_next.items)) {
      // reload tree
      if (!tagged_next.isInCache()) {
        this.props.actions.notifyLoading();
        this.props.actions.reloadTree(entry_point_id, tagged_next.items);
      }
      // reload entities
      if (!tagged_next.entities_ignore) {
        const params = parseRequestParams(request_params),
          subj_req_ids = params.subj_ids,
          options_arr = params.options_arr;

        let request_options = meta.request_options,
          subj_ids = meta.subj_ids || subj_req_ids;

        delete request_options["alike"];
        request_options['terms'] = tagged_next.items;
        request_options['offset'] = 0;
        this.props.actions.notifyLoadingEntities();

        this.props.actions.getEntities(
          entry_point_id, subj_ids, request_options, options_arr
        );
      }
    }

    if (tagged_current.items.length !== tagged_next.items.length) {
      let countTaggedBranch = 0;
      tagged_next.items.map(item => {
        if (termsIdsStructureIsLimb.includes(item))
          countTaggedBranch++;
      });
      this.props.actions.setCountTaggedBranch(countTaggedBranch);
    }
  }

  render() {
    const {terms, actions} = this.props,
      term = terms.tree.root,
      details = terms.details,
      tagged = terms.tagged,
      expanded = terms.expanded,
      info_expanded = terms.info_expanded,
      loading = terms.tree.loading,
      realPotential = terms.realPotential;

    return term ? (
        <TermsTreeItem key={term.id}
                       term={term}
                       details={details}
                       tagged={tagged}
                       expanded={expanded}
                       info_expanded={info_expanded}
                       realPotential={realPotential}
                       actions={actions}/>
      )
      : null
  }
}

const mapStateToProps = state => ({
  terms: state.terms,
  entities: state.entities
});

const mapDispatchToProps = dispatch => ({
  actions: bindActionCreators(ActionCreators, dispatch),
  dispatch: dispatch
});

export default connect(mapStateToProps, mapDispatchToProps)(TermsTree);
