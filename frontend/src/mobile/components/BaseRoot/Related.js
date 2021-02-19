import React, {Component} from 'react';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import Entities from '../Entities';
import ActionCreators from "../../actions";
import {View, Text} from 'react-native'


class Related extends Component {
  render() {
    const {entry_points, entry_point_id,} = this.props;
    let entry_point = entry_points[entry_point_id];

    return (
      <View><Text>Related</Text></View>
    )

    // return (
    //   <Entities entry_points={entry_points} entry_point_id={entry_point_id} />
    // );
  }
}

const mapStateToProps = state => ({
  entities: state.entities.items
});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(Related);
