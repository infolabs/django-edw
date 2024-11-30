import React from 'react';
import {listStyles} from '../../native_styles/entities';
import {renderEntityList, renderEntityItem, stylesComponent} from './base';


const styles = Object.assign({}, listStyles, stylesComponent);


export default function List(props) {
  function createItem(child, i) {
    return (
      <ListItem
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

  return renderEntityList(props, styles, createItem);
}

function ListItem(props) {
  const text = props.data.entity_name;

  return renderEntityItem(props, text, styles, null, null, true);
}
