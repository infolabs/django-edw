import React, { Component } from 'react';
import Dropdown from './Dropdown';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/Actions'


class Ordering extends Component {
  render() {
    const { mart_id, actions } = this.props,
          { dropdowns } = this.props.entities,
          { meta } = this.props.entities.items,
          { ordering } = dropdowns;

    let ret = <div></div>;
    if (ordering && Object.keys(ordering.options).length > 1) {
      ret = (
        <ul className="ex-inline">
          <li>
            <span>{gettext("Sort by")} &nbsp; </span>
          </li>
          <li>
            <Dropdown name='ordering'
                      mart_id={mart_id}
                      request_var={ordering.request_var}
                      request_options={meta.request_options}
                      subj_ids={meta.subj_ids}
                      open={ordering.open}
                      actions={actions}
                      selected={ordering.selected}
                      options={ordering.options}/>
          </li>
        </ul>
      )
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

export default connect(mapState, mapDispatch)(Ordering);
