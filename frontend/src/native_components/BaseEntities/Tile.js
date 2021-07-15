import React from 'react';
import {tileStyles as styles} from '../../native_styles/entities';
import {renderEntityTile, renderEntityItem, maxLengthDescriptionTile} from './base';


function Tile(props) {
  function createItem(child, i) {
    return <TileItem
            key={i}
            data={child}
            templateIsDataMart={props.templateIsDataMart}/>;
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


export default Tile;
