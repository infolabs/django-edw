import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import * as TermsTreeActions from '../actions/TermsTreeActions';


class Statistics extends Component {
  render() {
    const meta = this.props.entities.items.meta,
          { actions, mart_id } = this.props;

    let ret = <span></span>;
    if (meta.count) {
      const total = meta.count,
            offset = meta.offset,
            limit = meta.limit;

      let to = offset + limit;
      to = total < to ? total : to;

      ret = (
        <span>{offset + 1} - {to} {gettext("from")} {total}</span>
      );
    }
    return ret;
  }
}

function mapState(state) {
  return {
    entities: state.entities,
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(TermsTreeActions, dispatch),
    dispatch: dispatch
  };
}

export default connect(mapState, mapDispatch)(Statistics);
