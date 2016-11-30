import React, { Component } from 'react';

class List extends Component {
  render() {
    let data = this.props.data;
    return <div>{data.entity_name}</div>;
  }
}

class Tile extends Component {
  render() {
    let data = this.props.data;
    return <div className="view_tile">{data.entity_name}</div>;

  }
}

export const loader = {
  'list': List,
  'tile': Tile
}

