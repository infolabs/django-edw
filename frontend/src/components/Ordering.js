import React, {Component} from 'react';
import Dropdown from './Dropdown';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Actions from '../actions/index';


class Ordering extends Component {
  render() {
    const {entry_points, entry_point_id, actions} = this.props,
      {dropdowns} = this.props.entities,
      {meta} = this.props.entities.items,
      {ordering} = dropdowns;

    let ret = <div/>,
      request_options = {...meta.request_options, offset: 0}; //сбрасываем offset при переключении сортировки

    if (ordering && Object.keys(ordering.options).length > 1) {
      ret = (
        <div className="maincol-top__col ex-order-by ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>{gettext('Sort by')} &nbsp; </span>
            </li>
            <li>
              <Dropdown name="ordering"
                        entry_points={entry_points}
                        entry_point_id={entry_point_id}
                        request_var={ordering.request_var}
                        request_options={request_options}
                        subj_ids={meta.subj_ids}
                        open={ordering.open}
                        actions={actions}
                        selected={ordering.selected}
                        options={ordering.options}/>
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

export default connect(mapState, mapDispatch)(Ordering);
