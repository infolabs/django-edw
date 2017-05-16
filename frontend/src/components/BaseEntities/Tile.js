import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import 'marked';


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
    const { data, actions, descriptions } = this.props;
    actions.showDescription(data.id);
    if (!descriptions[data.id])
      actions.getEntityItem(data.entity_url);
  }

  handleMouseOut(e) {
    const { data, actions, descriptions } = this.props;
    actions.hideDescription(data.id);
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
    const { data, descriptions, position, meta } = this.props,
        url = data.extra && data.extra.url ? data.extra.url : data.entity_url,
        index = position + meta.offset;

    let li_class = "ex-catalog-item";
    if (descriptions.opened[data.id]) {
      li_class += " ex-state-description";
    }

    let characteristics = data.short_characteristics || [],
        marks = data.short_marks || [];

    // let related_data_marts = [];
    if (descriptions[data.id]) {
        characteristics = descriptions[data.id].characteristics || [];
        marks = descriptions[data.id].marks || [];
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
                    <strong>{child.name}:</strong>&nbsp;
                    {child.values.join("; ")}
                  </li>
              )}
            </ul>
          </div>
        </div>
      )
    }

    let ret = (

    <li className={li_class}
        data-horizontal-position={this.state.h_pos}
        data-vertical-position="center"
        data-index={index}
        onMouseOver={e => { ::this.handleMouseOver(e) } }
        onMouseOut={e => { ::this.handleMouseOut(e) } }>

      <div className="ex-catalog-item-block">
        {description_baloon}
        <div className="ex-wrap-action">
          <div className="ex-media" dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}}></div>

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
              <a href={url} title={data.entity_name}>{data.entity_name}</a>
            </h4>
          </div>
        </div>
      </div>
    </li>
    );

    return ret;
  }
}
