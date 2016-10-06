import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component, PropTypes } from 'react';
import * as RubricatorActions from '../actions/RubricatorActions'; //TermsTreeActions
import RubricatorItem from './RubricatorItem'; //TermsTreeItem

class Rubricator extends Component {

  componentDidMount() {
    this.props.actions.toggle();
    //this.props.actions.getTermsTree();
  }

  componentWillReceiveProps(nextProps) {
    //subscribe fetch to props change
    if (nextProps.terms && nextProps.terms.aux == 'toggle') {
      this.props.dispatch(RubricatorActions.getTermsTree(
          nextProps.terms.tagged_ids
      ));
    }
  }

  render() {
    const { terms, actions } = this.props;
    let terms_tree = [];
    if (typeof terms.terms_tree !== 'undefined')
      terms_tree = terms.terms_tree

    return (
    <div>
      <ul>
        {terms_tree.map(term =>
          <RubricatorItem key={term.id} //TermsTreeItem
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
    actions: bindActionCreators(RubricatorActions, dispatch),
    dispatch: dispatch
  };
}

export default connect(mapState, mapDispatch)(Rubricator);

