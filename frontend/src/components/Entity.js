import React, { Component } from 'react';

export default class Entity extends Component {
  render() {
    const entity = this.props.entity;
    return <div>{entity.entity_name}</div>;
  }
}
