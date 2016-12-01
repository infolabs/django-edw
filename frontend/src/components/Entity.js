import React, { Component } from 'react';
import { loader } from "./templates/loader";


export default class Entity extends Component {
  render() {
    const data = this.props.entity,
          component = loader[this.props.component];
    //console.log(component)
    return React.createElement(component, {data: data});
  }
}


