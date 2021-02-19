import React from 'react'
import {View} from 'react-native'
import ActionCreators from "../actions";
import {connect} from 'react-redux'
import {bindActionCreators} from "redux"
import Dropdown from "./Dropdown";


const Ordering = props => {
  const {entry_points, entry_point_id} = props,
        {dropdowns} = props.entities,
        {meta} = props.entities.items,
        {ordering} = dropdowns;

  let request_options = {...meta.request_options, offset: 0}; //сбрасываем offset при переключении сортировки

  if (ordering && Object.keys(ordering.options).length > 1) {
    return (
      <View style={{width: '50%'}}>
        <Dropdown name='ordering'
                  entry_points={entry_points}
                  entry_point_id={entry_point_id}
                  request_var={ordering.request_var}
                  request_options={request_options}
                  subj_ids={meta.subj_ids}
                  open={ordering.open}
                  selected={ordering.selected}
                  options={ordering.options}/>
      </View>
    )
  } else
    return null
};


const mapStateToProps = state => ({
  entities: state.entities
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Ordering);
