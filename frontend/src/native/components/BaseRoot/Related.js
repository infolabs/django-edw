import React from 'react';
import Entities from '../Entities';


function Related(props) {
  const {entry_points, entry_point_id} = props;

  return (
    <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
  );
}

export default Related;
