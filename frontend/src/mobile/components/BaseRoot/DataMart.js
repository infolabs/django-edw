import React, {Component} from 'react'
import {connect} from 'react-redux'
import Ordering from "../Ordering"
import Entities from "../Entities"
import ActionCreators from "../../actions"
import {bindActionCreators} from "redux"


export class DataMart extends Component {

  render(){
    const {entry_point_id, entry_points} = this.props;

    return (
      <>
        <Ordering entry_points={entry_points} entry_point_id={entry_point_id} />
        <Entities entry_points={entry_points} entry_point_id={entry_point_id} />
      </>
    )
  }
}

const mapStateToProps = state => ({});
const mapDispatchToProps = dispatch => bindActionCreators(ActionCreators, dispatch);

export default connect(mapStateToProps, mapDispatchToProps)(DataMart);
