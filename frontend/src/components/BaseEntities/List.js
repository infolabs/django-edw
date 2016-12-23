import React, { Component } from 'react';

// Container

export default class List extends Component {
  render() {
    const { items, actions, loading, descriptions, meta } = this.props;
    let entities_class = "entities list-items";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    return (
      <ul className={entities_class}>
        {items.map(
          (child, i) => 
          <ListItem key={i} data={child} actions={actions} descriptions={descriptions} position={i} meta={meta}/>
        )}
      </ul>
    );
  }
}

// Element

class ListItem extends Component {
  render() {
    const { data, position, meta } = this.props,
        url = data.extra && data.extra.url ? data.extra.url : data.entity_url,
        index = position + meta.offset;

    return (
      <li data-index={index}>
        <a href={url}>{data.entity_name}</a>
      </li>
    );
  }
}
