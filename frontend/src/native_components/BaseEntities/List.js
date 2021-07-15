import React from 'react';
import {listStyles as styles} from '../../native_styles/entities';
import {renderEntityList, renderEntityItem} from './base';


function List(props) {
  function createItem(child, i) {
    return <ListItem
            key={i}
            data={child}
            templateIsDataMart={props.templateIsDataMart}/>;
  }
  return renderEntityList(props, styles, createItem);
}


function ListItem(props) {
  const text = props.data.entity_name;
  const badge = null;

  return renderEntityItem(props, text, badge, styles);
}


export default List;
