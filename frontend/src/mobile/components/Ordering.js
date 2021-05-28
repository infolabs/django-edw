import React from 'react';
import {useSelector} from 'react-redux';
import Dropdown from './Dropdown';


function Ordering(props) {
  const entities = useSelector(state => state.entities);
  const {entry_points, entry_point_id} = props,
    {dropdowns} = entities,
    {meta} = entities.items,
    {ordering} = dropdowns;

  const request_options = {...meta.request_options, offset: 0}; //сбрасываем offset при переключении сортировки

  if (ordering && Object.keys(ordering.options).length > 1 && meta.count > 1) {
    return (
      <Dropdown name={'ordering'}
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
  return null;
}


export default Ordering;
