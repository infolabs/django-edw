import React, { Component } from 'react';
import BtnGroup from './BtnGroup';
import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import Actions from '../actions/index';


class ViewComponents extends Component {
  render() {
    const { entry_point_id, actions } = this.props,
          { dropdowns } = this.props.entities,
          { meta } = this.props.entities.items,
          { view_components } = dropdowns;

    let ret = <div/>,
        request_options = {...meta.request_options, offset: 0}; //сбрасываем offset при переключении view components

    if (view_components && Object.keys(view_components.options).length > 1) {

      // if the selected component isn't in the options list, select the first one
      let selected = view_components.selected;

      //const values = Object.values(view_components.options); not work in IE11
      // IE 11 hack
      const values = Object.keys(view_components.options).map(idx => view_components.options[idx]);

      if (values.length && values.indexOf(selected) < 0)
        selected = values[0];

      ret = (
        <ul className="ex-inline">
          <li>
            <span>{gettext('View as')} &nbsp; </span>
          </li>
          <li>
            <BtnGroup
                name="view_components"
                request_var={view_components.request_var}
                entry_point_id={entry_point_id}
                subj_ids={meta.subj_ids}
                request_options={request_options}
                open={view_components.open}
                actions={actions}
                selected={selected}
                options={view_components.options}
            />
          </li>
        </ul>
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

export default connect(mapState, mapDispatch)(ViewComponents);
