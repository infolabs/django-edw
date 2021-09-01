import React, {Component} from 'react';
import Dropdown from './Dropdown';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Actions from '../actions/index';


class Limits extends Component {
  render() {
    const {entry_point_id, actions} = this.props,
      {dropdowns} = this.props.entities,
      {meta} = this.props.entities.items,
      {limits} = dropdowns;

    let ret = <div/>,
      limit_options = {};

    if (meta.count <= 1)
      return ret;

    let max_opt_value = 0;
    if (limits) {
      // cut limits lower than count
      let max_value = 0;

      for (const key of Object.keys(limits.options)) {
        const value = limits.options[key];
        max_opt_value = value > max_opt_value ? value : max_opt_value;
        if (meta.count < max_opt_value)
          break;

        if (key === meta.selected || value <= meta.count) {
          max_value = value > max_value ? value : max_value;
          limit_options[key] = value;
        }
      }
      if (max_value < meta.count && meta.count < max_opt_value)
        limit_options[max_opt_value] = gettext('All');
    }

    if (limits && Object.keys(limit_options).length > 1) {
      let selectedLabel = limits.selected >= max_opt_value ? gettext('All') : limits.selected;
      ret = (
        <div className="maincol-top__col ex-howmany-items ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>{gettext('Quantity')} &nbsp; </span>
            </li>
            <li>
              <Dropdown name="limits"
                        entry_point_id={entry_point_id}
                        request_var={limits.request_var}
                        request_options={meta.request_options}
                        subj_ids={meta.subj_ids}
                        open={limits.open}
                        actions={actions}
                        selected={selectedLabel}
                        count={meta.count}
                        options={limit_options}/>

            </li>
          </ul>
        </div>
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
    dispatch: dispatch,
  };
}

export default connect(mapState, mapDispatch)(Limits);
