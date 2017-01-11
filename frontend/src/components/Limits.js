import React, { Component } from 'react';
import Dropdown from './Dropdown';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import * as TermsTreeActions from '../actions/TermsTreeActions';

class Limits extends Component {
  render() {
    const { mart_id, actions } = this.props,
          { dropdowns } = this.props.entities,
          { meta } = this.props.entities.items,
          { limits } = dropdowns;

    let ret = <div></div>,
        limit_options = {};

    if (limits) {
      // cut limits lower than count
      let max_opt_value = 0,
          max_value = 0;
      for (const key of Object.keys(limits.options)) {
        const value = limits.options[key]
        max_opt_value = value > max_opt_value ? value : max_opt_value;
        if (key == meta.selected || value <= meta.count) {
          max_value = value > max_value ? value : max_value;
          limit_options[key] = value;
        }
      }
      if (max_value < meta.count && meta.count < max_opt_value)
        limit_options[meta.count] = gettext("All");
    }

    if (limits && Object.keys(limit_options).length > 1) {
      ret = (
        <ul className="ex-inline">
          <li>
            <span>{gettext("Quantity")} &nbsp; </span>
          </li>
          <li>
            <Dropdown name='limits'
                      mart_id={mart_id}
                      request_var={limits.request_var}
                      request_options={meta.request_options}
                      subj_ids={meta.subj_ids}
                      open={limits.open}
                      actions={actions}
                      selected={limits.selected}
                      count={meta.count}
                      options={limit_options}/>

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
    actions: bindActionCreators(TermsTreeActions, dispatch),
    dispatch: dispatch
  };
}

export default connect(mapState, mapDispatch)(Limits);
