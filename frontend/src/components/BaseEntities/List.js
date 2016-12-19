import React, { Component } from 'react';

// Container

export default class List extends Component {
  render() {
    const { items, actions, loading, descriptions } = this.props;
    let entities_class = "entities list-items";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    return (
      <ul className={entities_class}>
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
