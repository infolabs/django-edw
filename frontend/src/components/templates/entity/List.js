import React, { Component } from 'react';

// Container

export default class List extends Component {
  render() {
    const { items, actions, descriptions } = this.props;

    return (
      <ul className='list-items'>
        {items.map(
          (child, i) => 
          <ListItem key={i} data={child} actions={actions} descriptions={descriptions}/>
        )}
      </ul>
    );
  }
}

// Element

class ListItem extends Component {
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
