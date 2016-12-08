import React, { Component } from 'react';

export default class Tile extends Component {

  handleMouseOver(e) {
    const { data, actions, descriptions } = this.props;
    e.preventDefault();
    e.stopPropagation();
    actions.showDescription(data.id);
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
    if (descriptions[data.id]) {
      li_class += " ex-state-description";
    }

    const short_characteristics = data.short_characteristics || [],
          short_marks = data.short_marks || [];

    let ret = (
    <li className={li_class}
        onMouseOver={e => { ::this.handleMouseOver(e) } }
        onMouseOut={e => { ::this.handleMouseOut(e) } }>
      <div className="ex-catalog-item-block">
        <div className="ex-description-wrapper">
          <div className="ex-baloon">
            <div className="ex-arrow"></div>
            <ul className="ex-attrs">
              {short_characteristics.map(
                (child, i) =>
                  <li key={i} className="lead">
                    {child.name}
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
            {short_marks.map(
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
