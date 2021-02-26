import React, {Component} from 'react'
import {View, StyleSheet} from 'react-native'
import {connect} from 'react-redux'
import Ordering from "../Ordering"
import FilterBtn from "../FilterBtn"
import Entities from "../Entities"
import ActionCreators from "../../actions"
import {bindActionCreators} from "redux"
import platformSettings from "../../constants/Platform";


export class DataMart extends Component {

  render(){
    const {entry_point_id, entry_points} = this.props;

    const {deviceHeight, deviceWidth} = platformSettings;

    const styles = StyleSheet.create({
      sortAndFilteredView: {
        width: deviceWidth,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 15,
      }
    });

    return (
      <>
        <View style={styles.sortAndFilteredView}>
          <Ordering entry_points={entry_points} entry_point_id={entry_point_id} />
          <FilterBtn entry_points={entry_points} entry_point_id={entry_point_id} />
        </View>
        <Entities entry_points={entry_points} entry_point_id={entry_point_id} />
      </>
    )
  }
}

const mapStateToProps = state => ({});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(DataMart);
