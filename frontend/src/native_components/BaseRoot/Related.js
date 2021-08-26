import React from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Entities from 'native_components/Entities';
import ActionCreators from '../../actions';


function Related(props) {
  const {entry_points, entry_point_id, fromRoute, dataMartName, containerSize} = props;

  return (
    <Entities {...{
      entry_points,
      entry_point_id,
      fromRoute,
      dataMartName,
      containerSize,
    }}/>
  );
}

const mapStateToProps = state => ({
  entities: state.entities.items,
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Related);
