import React, {Component} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import TermsTreeItem from './TermsTreeItem';
import ActionCreators from "../actions";
import parseRequestParams from "../utils/parseRequestParams"


class TermsTree extends Component {

  componentDidMount() {
    const entry_points = this.props.entry_points,
      entry_point_id = this.props.entry_point_id,
      request_params = entry_points[entry_point_id.toString()].request_params || [];

    const params = parseRequestParams(request_params),
      term_ids = params.term_ids;

    this.props.actions.notifyLoading();
    this.props.actions.readTree(entry_point_id, term_ids);
  }

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
