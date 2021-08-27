import React from 'react';
import {tileStyles as styles} from '../../native_styles/entities';
import {renderEntityTile, renderEntityItem, maxLengthDescriptionTile} from './base';


export default function Tile(props) {
  function createItem(child, i) {
    return (
      <TileItem
        key={i}
        data={child}
        meta={props.meta}
        fromRoute={props.fromRoute}
        toRoute={props.toRoute}
        templateIsDataMart={props.templateIsDataMart}
        containerSize={props.containerSize}
        items={props.items}/>
    );
  }

  return renderEntityTile(props, styles, createItem);
}

function TileItem(props) {
  const text = props.data.entity_name.length > maxLengthDescriptionTile
    ? `${props.data.entity_name.slice(0, maxLengthDescriptionTile)}...`
    : props.data.entity_name;

  const badge = null;

  return renderEntityItem(props, text, badge, styles);
}
