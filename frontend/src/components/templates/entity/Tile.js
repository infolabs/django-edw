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
    const { data, descriptions } = this.props;

    let li_class = "ex-catalog-item";
    if (descriptions[data.id]) {
      li_class += " ex-state-description";
    }

    let ret = (
    <li className={li_class}
        onMouseOver={e => { ::this.handleMouseOver(e) } }
        onMouseOut={e => { ::this.handleMouseOut(e) } }>
      <div className="ex-catalog-item-block">
        <div className="ex-description-wrapper">
          <div className="ex-baloon ex-baloon-hide">
            <div className="ex-arrow"></div>
            <ul className="ex-attrs">
              <li className="lead">
               {data.entity_name}
              </li>
            </ul>
          </div>
        </div>
        <div className="ex-action-wrapper">
          <div className="ex-wrap-img-container">
            <div className="ex-wrap-img-container-inner">
              <div className="ex-wrap-img">
                <a href={data.entity_url}
                   title={data.entity_name}
                   dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}} />
              </div>
            </div>
          </div>
          <ul className="ex-ribbons">
            <li className="ex-wrap-ribbon">
              <div className="ex-ribbon">{data.short_marks.name}</div>
            </li>
          </ul>
          <div className="ex-wrap-title">
            <h4 className="ex-title">
              <a href={data.media}
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
