import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import marked from 'marked';


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

class TileItem extends Component {

  constructor() {
    super();
    this.state = {
      h_pos: null,
    };
  }

  handleMouseOver(e) {
    this.toggleDescription(e);
  }

  handleMouseOut(e) {
    this.toggleDescription(e);
  }

  handleMouseClick(e) {
    const { data, actions, meta } = this.props;
    if (data.extra.group_size) {
      actions.notifyLoadingEntities();
      actions.expandGroup(data.id, meta);
      e.preventDefault();
      e.stopPropagation();
    }
  }

  toggleDescription(e) {
    const { data, actions, meta, descriptions } = this.props,
          id = data.id;

    if (this.getIsHover(e.clientX, e.clientY)) {
      actions.showDescription(id);

      if (data.extra.group_size && !meta.alike && !descriptions.groups[id])
        actions.getEntityItem(data, meta);

      if (!data.extra.group_size && !descriptions[id])
        actions.getEntityItem(data);
    } else {
      actions.hideDescription(id);
    }
  }

  getIsHover(clientX, clientY) {
    const area = ReactDOM.findDOMNode(this),
          areaRect = area.getBoundingClientRect(),
          posX = clientX - areaRect.left,
          posY = clientY - areaRect.top;

    return posX >= 0 && posY >= 0 && posX <= areaRect.width && posY <= areaRect.height;
  }

  componentDidMount(x, y, z) {
    const area = ReactDOM.findDOMNode(this),
          info = area.getElementsByClassName("ex-description-wrapper")[0];
          // areaRect = area.getBoundingClientRect(),
    if (info) {
      const infoRect = info.getBoundingClientRect(),
            window_width = window.innerWidth,
            width = 250, // todo: calculate width
            left = infoRect.right,
            h_pos = window_width < left + width ? "right" : "left";
      this.setState({"h_pos": h_pos});
    }
  }

  render() {
    const { data, position, meta, descriptions } = this.props,
          url = data.extra && data.extra.url ? data.extra.url : data.entity_url,
          index = position + meta.offset,
          group_size = data.extra.group_size || 0;

    let group_digit = "";
    if (group_size) {
      group_digit = (
        <span className="ex-digit">{group_size}</span>
      );
    }

    let li_class = "ex-catalog-item";
    if (descriptions.opened[data.id]) {
      li_class += " ex-state-description";
    }

    let characteristics = data.short_characteristics || [],
        marks = data.short_marks || [];

    let descriptions_data = group_size ? descriptions.groups : descriptions;
    // let related_data_marts = [];
    if (descriptions_data[data.id]) {
        characteristics = descriptions_data[data.id].characteristics || [];
        marks = descriptions_data[data.id].marks || [];
        // related_data_marts = descriptions[data.id].marks || [];
    }

    let description_baloon = "";
    if (characteristics.length) {
      description_baloon = (
        <div className="ex-description-wrapper">
          <div className="ex-baloon">
            <div className="ex-arrow"></div>
            <ul className="ex-attrs">
              {characteristics.map(
                (child, i) =>
                  <li data-path={child.path} key={i}
                    data-view-class={child.view_class.join(" ")}>
                    <strong>{child.name}:&nbsp;</strong>
                    {child.values.join("; ")}
                  </li>
              )}
            </ul>
          </div>
        </div>
      );
    }

    const title = group_size && !meta.alike ? data.extra.group_name : data.entity_name;

    const item_content = (
      <div className="ex-wrap-action">
        <div className="ex-media"
             dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}}>
        </div>

        <ul className="ex-ribbons">
          {marks.map(
            (child, i) =>
              <li className="ex-wrap-ribbon"
                  key={i}
                  data-name={child.name}
                  data-path={child.path}
                  data-view-class={child.view_class.join(" ")}>
                <div className="ex-ribbon">{child.values.join(", ")}</div>
              </li>
          )}
        </ul>

        <div className="ex-wrap-title">
          <h4 className="ex-title">
            <a href={url} title={title}>{title}</a>
          </h4>
        </div>
      </div>
    );

    let item_block = (
        <div className="ex-catalog-item-block"
             onClickCapture={e => { ::this.handleMouseClick(e); } }>
          {description_baloon}
          {item_content}
        </div>
    );

    if (group_size) {
      item_block = (
        <div className="ex-catalog-item-block ex-catalog-item-variants"
             onClickCapture={e => { ::this.handleMouseClick(e); } }>
          <div>
            <div>
              {description_baloon}
              {group_digit}
              {item_content}
            </div>
          </div>
        </div>
      );
    }

    let ret = (
      <li className={li_class}
          data-horizontal-position={this.state.h_pos}
          data-vertical-position="center"
          data-index={index}
          onMouseOver={e => { ::this.handleMouseOver(e); } }
          onMouseOut={e => { ::this.handleMouseOut(e); } }>
          {item_block}
      </li>
    );

    return ret;
  }
}
