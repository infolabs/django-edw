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
          index = position + meta.offset,
          marks = data.short_marks || [];

    return (
      <li>
        <h4>
          <a href={url} title={data.entity_name}>{data.entity_name}</a>&nbsp;
        </h4>
        <span className="tags">
          <small>
            {marks.map(
              (child, i) =>
                <span className="ex-wrap-ribbon"
                    key={i}
                    data-name={child.name}
                    data-path={child.path}
                    data-view-class={child.view_class.join(" ")}><i className="fa fa-tag"></i>&nbsp;
                  <span className="ex-ribbon">{child.values.join(", ")} </span>
                </span>
            )}
          </small>
        </span>
      </li>
    );
  }
}
