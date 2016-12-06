import React, { Component } from 'react';

const templates = require('templates/entity').default();

export default class Entity extends Component {
  render() {
    const data = this.props.entity,
          component = templates[this.props.component];
    //console.log(component)
    return React.createElement(component, {data: data});
  }
}


