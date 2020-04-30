import React, { Component } from 'react';
import TileItemMixin from "./TileItemMixin";


// Container

export default class Tile extends Component {

  render() {
    const { items, actions, loading, descriptions, meta } = this.props;
    let entities_class = "entities ex-tiles";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    return (
      <ul className={entities_class}>
        {items.map(
          (child, i) =>
          <TileItem key={i} data={child} actions={actions} descriptions={descriptions} position={i} meta={meta}/>
        )}
      </ul>
    );
  }
}

// Element

class TileItem extends TileItemMixin {

  render() {
    const { data, position, meta, descriptions } = this.props,
          index = position + meta.offset,
          groupSize = data.extra && data.extra.group_size ? data.extra.group_size : 0;

    let groupDigit;
    if (groupSize) {
      groupDigit = (
        <span className="ex-digit">{groupSize}</span>
      );
    }

    let liClass = "ex-catalog-item";
    if (descriptions.opened[data.id])
      liClass += " ex-state-description";

    let characteristics = data.short_characteristics || [],
        marks = data.short_marks || [];

    let descriptions_data = groupSize ? descriptions.groups : descriptions;
    // let related_data_marts = [];
    if (descriptions_data[data.id]) {
        characteristics = descriptions_data[data.id].characteristics || [];
        marks = descriptions_data[data.id].marks || [];
        // related_data_marts = descriptions[data.id].marks || [];
    }

    const descriptionBaloon = this.getDescriptionBaloon(data, characteristics),
          title = groupSize && !meta.alike ? data.extra.group_name : data.entity_name,
          itemContent = this.getItemContent(data, title, marks),
          itemBlock = this.getItemBlock(descriptionBaloon, itemContent, groupDigit, groupSize);

    return(
      <li className={liClass}
          data-horizontal-position={this.state.h_pos}
          data-vertical-position="center"
          data-index={index}
          onMouseOver={e => { ::this.handleMouseOver(e); } }
          onMouseOut={e => { ::this.handleMouseOut(e); } }>
          {itemBlock}
      </li>
    );
  }
}
