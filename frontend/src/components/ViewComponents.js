import React, { Component } from 'react';
import BtnGroup from './BtnGroup';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index'


class ViewComponents extends Component {
  render() {
    const { entry_point_id, actions } = this.props,
          { dropdowns } = this.props.entities,
          { meta } = this.props.entities.items,
          { view_components } = dropdowns;

    let ret = <div></div>;
    if (view_components && Object.keys(view_components.options).length > 1) {

      ret = (
        <ul className="ex-inline">
          <li>
            <span>{gettext("View as")} &nbsp; </span>
          </li>
          <li>
            <BtnGroup
                name='view_components'
                request_var={view_components.request_var}
                entry_point_id={entry_point_id}
                subj_ids={meta.subj_ids}
                request_options={meta.request_options}
                open={view_components.open}
                actions={actions}
                selected={view_components.selected}
                options={view_components.options}
            />
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

export default connect(mapState, mapDispatch)(ViewComponents);
