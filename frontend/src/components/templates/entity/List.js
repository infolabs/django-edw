import React, { Component } from 'react';

export default class List extends Component {
  render() {
    let data = this.props.data;
    return (
      <li>
        <a href={data.entity_url}>{data.entity_name}</a>
      </li>
    );
  }
}