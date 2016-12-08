import React, { Component } from 'react';

// Container

export default class Tile extends Component {

  render() {
    const { items, actions, descriptions } = this.props;

    return (
      <ul className="ex-catalog-grid-4-col">
        {items.map(
          (child, i) => 
          <TileItem key={i} data={child} actions={actions} descriptions={descriptions}/>
        )}
      </ul>
    );
  }
}

// Element

class TileItem extends Component {

  handleMouseOver(e) {
    const { data, actions, descriptions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.showDescription(data.id);
    if (!descriptions[data.id])
      actions.getEntityItem(data.entity_url);
  }

  handleMouseOut(e) {
    const { data, actions, descriptions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.hideDescription(data.id);
  }

  render() {
    const { data, descriptions } = this.props,
          url = data.extra && data.extra.url ? data.extra.url : data.entity_url;

    let li_class = "ex-catalog-item";
    if (descriptions.opened[data.id]) {
      li_class += " ex-state-description";
    }

    let characteristics = data.short_characteristics || [],
        marks = data.short_marks || [];

    let related_data_marts = []
    if (descriptions[data.id]) {
        characteristics = descriptions[data.id].characteristics || [];
        marks = descriptions[data.id].marks || [];
        related_data_marts = descriptions[data.id].marks || [];
    }

    let ret = (
    <li className={li_class}
        onMouseOver={e => { ::this.handleMouseOver(e) } }
        onMouseOut={e => { ::this.handleMouseOut(e) } }>
      <div className="ex-catalog-item-block">
        <div className="ex-description-wrapper">
          <div className="ex-baloon">
            <div className="ex-arrow"></div>
            <ul className="ex-attrs">
              <li className="lead">
                {data.entity_name}
              </li>
              {characteristics.map(
                (child, i) =>
                  <li key={i}>
                    <strong>{child.name}: </strong>
                    {child.values.join(",")}
                  </li>
              )}
            </ul>
          </div>
        </div>
        <div className="ex-action-wrapper">
          <div className="ex-wrap-img-container">
            <div className="ex-wrap-img-container-inner">
              <div className="ex-wrap-img">
                <a href={url}
                   title={data.entity_name}
                   dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}} />
              </div>
            </div>
          </div>
          <ul className="ex-ribbons">
            {marks.map(
              (child, i) =>
                <li className="ex-wrap-ribbon"
                    key={i}
                    data-name={child.name}
                    data-path={child.path}
                    data-view-class={child.view_class.join(" ")}>
                  <div className="ex-ribbon">{child.values.join(",")}</div>
                </li>
            )}
          </ul>
          <div className="ex-wrap-title">
            <h4 className="ex-title">
              <a href={url}
                 title={data.entity_name}
                 className="ex-js-open">
                {data.entity_name}
              </a>
            </h4>
          </div>
        </div>
      </div>
    </li>
    );

    return ret;
  }
}
