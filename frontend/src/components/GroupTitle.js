import React, {Component} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import ActionCreators from "../actions";


class GroupTitle extends Component {
  handleMouseClick() {
    const {meta} = this.props.entities.items,
      mart_id = meta.data_mart.id,
      {subj_ids} = meta;
    let {request_options} = meta;
    delete request_options.alike;
    delete request_options.offset;
    this.props.notifyLoadingEntities();
    const params = {
      options_obj: request_options,
      closeGroup: true,
      mart_id,
      subj_ids
    };
    this.props.getEntities(params);
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
