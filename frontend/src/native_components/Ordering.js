import React from 'react';
import ActionCreators from '../actions';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Dropdown from './Dropdown';


function Ordering(props) {
  const {entry_points, entry_point_id, entities} = props,
    {dropdowns} = entities,
    {meta} = entities.items,
    {ordering} = dropdowns;

  let request_options = {...meta.request_options, offset: 0}; //сбрасываем offset при переключении сортировки

  if (ordering && Object.keys(ordering.options).length > 1 && meta.count > 1) {
    return (
      <Dropdown name="ordering"
                entry_points={entry_points}
                entry_point_id={entry_point_id}
                request_var={ordering.request_var}
                request_options={request_options}
                subj_ids={meta.subj_ids}
                open={ordering.open}
                selected={ordering.selected}
                options={ordering.options}/>
    );
  }
  return <></>;
}


const mapStateToProps = state => ({
  entities: state.entities,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(Ordering);
