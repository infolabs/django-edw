import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index';


class Statistics extends Component {
  render() {
    const meta = this.props.entities.items.meta;

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
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}

export default connect(mapState, mapDispatch)(Statistics);
