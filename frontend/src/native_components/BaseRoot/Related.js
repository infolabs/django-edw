import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Entities from '../Entities';
import ActionCreators from '../../actions';


function Related(props) {
  const {entry_points, entry_point_id} = props;

  return (
    <Entities entry_points={entry_points} entry_point_id={entry_point_id}/>
  );
}


const mapStateToProps = state => ({
  entities: state.entities.items,
});

const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);


export default connect(mapStateToProps, mapDispatchToProps)(Related);
