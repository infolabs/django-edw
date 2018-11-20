import React, { Component } from 'react';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index';


class GroupTitle extends Component {
  handleMouseClick() {
    const meta = this.props.entities.items.meta,
          actions = this.props.actions,
          mart_id = meta.data_mart.id,
          subj_ids = meta.subj_ids;
    let request_options = meta.request_options;
    delete request_options["alike"];
    delete request_options["offset"];
    actions.notifyLoadingEntities();
    actions.getEntities(mart_id, subj_ids, request_options);
  }

  render() {
    const alike = this.props.entities.items.meta.alike,
          loading = this.props.entities.items.loading,
          className = (loading ? " ex-state-loading" : "");
    let ret = null;
    if (alike) {
      ret = (
        <span className={className}>
          {alike.group_name}
          <i onClick={e => { ::this.handleMouseClick(); } }
             className="ex-icon-reset"></i>
        </span>
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

export default connect(mapState, mapDispatch)(GroupTitle);
