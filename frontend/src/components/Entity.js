import React, { Component } from 'react';

const templates = require('templates/entity').default();

export default class Entity extends Component {
  render() {
    const { entity, descriptions, actions } = this.props,
          component = templates[this.props.component];
    //console.log(component)
    return React.createElement(
      component, {data: entity, actions: actions, descriptions: descriptions}
    );
  }
}


