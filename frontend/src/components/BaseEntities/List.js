import React, { Component } from 'react';
import ListItemMixin from "./ListItemMixin";


// Container

export default class List extends Component {

  render() {
    const { items, actions, loading, descriptions, meta } = this.props;
    let entities_class = "entities list-items";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    return (
      <div className={entities_class}>
        {items.map(
          (child, i) =>
          <ListItem
              key={i}
              data={child}
              actions={actions}
              loading={loading}
              descriptions={descriptions}
              position={i}
              meta={meta}
          />
        )}
      </div>
    );
  }
}

// Element

class ListItem extends ListItemMixin(Component) {

  render() {
    const { data, meta, descriptions } = this.props,
          url = data.extra && data.extra.url ? data.extra.url : data.entity_url,
          groupSize = data.extra && data.extra.group_size ? data.extra.group_size : 0;

    let groupDigit = "";
    if (groupSize) {
      groupDigit = (
        <div className="ex-pack">
          <span className="ex-digit">{groupSize}</span>
          <div><div><div></div></div></div>
        </div>
      );
    }

    let characteristics = data.short_characteristics || [],
        marks = data.short_marks || [];

    // let related_data_marts = [];
    if (descriptions[data.id]) {
      characteristics = descriptions[data.id].characteristics || [];
      marks = descriptions[data.id].marks || [];
      // related_data_marts = descriptions[data.id].marks || [];
    }

    const className = "ex-catalog-item list-item" + (groupSize ? " ex-catalog-item-variants" : "") +
          (descriptions.opened[data.id] ? " ex-state-description" : "");

    const exAttrs = this.getExAttrs(data, characteristics),
          exTags = this.getExTags(marks),
          descriptionBaloon = this.getDescriptionBaloon(data, characteristics, marks, descriptions, exAttrs, exTags) || "",
          title = groupSize && !meta.alike ? data.extra.group_name : data.entity_name,
          itemBlock = this.getItemBlock(url, data, title, descriptionBaloon),
          itemContent = this.getItemContent(url, data, itemBlock, marks);

    return (
      <div className={className}
         onMouseOver={e => this.handleMouseOver(e)}
         onMouseOut={e => this.handleMouseOut(e)}
         style={{minHeight: this.state.minHeight}}>
         {groupDigit}
         {itemContent}
      </div>
    );
  }
}
