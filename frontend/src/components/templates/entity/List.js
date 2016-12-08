import React, { Component } from 'react';

export default class List extends Component {
  render() {
    const data = this.props.data,
          url = data.extra && data.extra.url ? data.extra.url : data.entity_url;

    return (
      <li>
        <a href={url}>{data.entity_name}</a>
      </li>
    );
  }
}
