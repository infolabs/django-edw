import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import  marked from 'marked';


const TOGGLE_DESCRIPTION_DELAY = 100;

// Container

export default class List extends Component {

  render() {
    const { items, actions, loading, descriptions, meta } = this.props;
    let entities_class = "entities list-items";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    return (
      <div className={entities_class}>
        {items.map(
          (child, i) =>
          <ListItem
              key={i}
              data={child}
              actions={actions}
              loading={loading}
              descriptions={descriptions}
              position={i}
              meta={meta}
          />
        )}
      </div>
    );
  }
}

// Element

class ListItem extends Component {

  state = {
    minHeight: 0,
    isHover: false
  };

  handleMouseOver(e) {
    this.toggleDescription(e);
  }

  handleMouseOut(e) {
    this.toggleDescription(e);
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.props.loading !== prevProps.loading) {
      this.setState({minHeight: 'auto'});
    }
  }

  toggleDescription(e) {
    const { data, actions, descriptions } = this.props,
          id = data.id,
          lastIsHover = this.getIsHover(e.clientX, e.clientY);

    this.setState({isHover: lastIsHover});

    let context = this;
    setTimeout(function() {
      const { isHover } = context.state;

      if (lastIsHover === isHover) {
        if (isHover) {
          const area = ReactDOM.findDOMNode(context),
            areaRect = area.getBoundingClientRect();

          context.setState({minHeight: areaRect.height});

          actions.showDescription(id);
          if (!descriptions[id]) {
            actions.getEntityItem(data);
          }
        } else {
          actions.hideDescription(id);
        }
      }
    }, TOGGLE_DESCRIPTION_DELAY);
  }

  getIsHover(clientX, clientY) {
    const area = ReactDOM.findDOMNode(this),
          areaRect = area.getBoundingClientRect(),
          posX = clientX - areaRect.left,
          posY = clientY - areaRect.top;

    return posX >= 0 && posY >= 0 && posX <= areaRect.width && posY <= areaRect.height;
  }

  render() {
    const { data, descriptions, position, meta } = this.props,
        url = data.extra && data.extra.url ? data.extra.url : data.entity_url,
        index = position + meta.offset;

    let item_wrapper_class = "wrap-list-item";
    if (descriptions.opened[data.id]) {
      item_wrapper_class += " is-active";
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
          <ul className="ex-tags">
            {marks.map(
              (child, i) =>
                <li className="ex-tag"
                    key={i}
                    data-name={child.name}
                    data-path={child.path}
                    data-view-class={child.view_class.join(" ")}>
                  <i className="fa fa-tag"></i>&nbsp;
                  {child.values.join(", ")}
                </li>
            )}
          </ul>
        </div>
      )
    }

    return (
      <div className="ex-catalog-item list-item"
         onMouseOver={e => this.handleMouseOver(e)}
         onMouseOut={e => this.handleMouseOut(e)}
         style={{minHeight: this.state.minHeight}}>

        <div className={item_wrapper_class}>
          <div className="row">
              <div className="col-md-3">
                <a href={url}>
                  <div className="ex-media" dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}}/>
                </a>
              </div>

            <div className="col-md-9">
              <a href={url}>
                <h4>{data.entity_name}</h4>
              </a>
              {descriptions.opened[data.id] && description_baloon}
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
                  <div className="ex-ribbon">{child.values.join(", ")}</div>
                </li>
            )}
          </ul>
        </div>
      </div>
    );
  }
}
