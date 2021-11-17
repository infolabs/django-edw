import React, {Component} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import ActionCreators from "../actions";


class GroupTitle extends Component {
  handleMouseClick() {
    const meta = this.props.entities.items.meta,
      mart_id = meta.data_mart.id,
      subj_ids = meta.subj_ids;
    let request_options = meta.request_options;
    delete request_options.alike;
    delete request_options.offset;
    this.props.notifyLoadingEntities();
    this.props.getEntities(mart_id, subj_ids, request_options, [], false, true);
  }

  render() {
    const alike = this.props.entities.items.meta.alike,
      loading = this.props.entities.items.loading,
      className = (loading ? ' ex-state-loading' : '');
      return alike ? (
        <span className={className}>
          {alike.group_name}
          <i onClick={e => {::this.handleMouseClick()}} className="ex-icon-reset"/>
        </span>
      ) : null
  }
}


const mapStateToProps = state => ({
  entities: state.entities
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(GroupTitle);
