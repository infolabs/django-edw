import React from 'react';
import ReactDOM from 'react-dom';
import marked from 'marked';


const TileItemMixin = Base => class extends Base {

  constructor(){
    super();
    this.state = {
      h_pos: null,
    };
  }

  handleMouseOver(e){
    this.toggleDescription(e);
  }

  handleMouseOut(e){
    this.toggleDescription(e);
  }

  handleMouseClick(e){
    const {data, actions, meta} = this.props;
    if (data.extra && data.extra.group_size) {
       actions.notifyLoadingEntities();
       actions.expandGroup(data.id, meta);
       e.preventDefault();
       e.stopPropagation();
    }
  }

  toggleDescription(e){
    const {data, actions, meta, descriptions} = this.props,
          id = data.id;

    if (this.getIsHover(e.clientX, e.clientY)) {
      actions.showDescription(id);

      if (data.extra && data.extra.group_size && !meta.alike && !descriptions.groups[id])
        actions.getEntityItem(data, meta);

      if ((data.extra && !data.extra.group_size) && !descriptions[id])
        actions.getEntityItem(data);

    } else
      actions.hideDescription(id);
  }

  getIsHover(clientX, clientY){
    const area = ReactDOM.findDOMNode(this),
          areaRect = area.getBoundingClientRect(),
          posX = clientX - areaRect.left,
          posY = clientY - areaRect.top;

    return posX >= 0 && posY >= 0 && posX <= areaRect.width && posY <= areaRect.height;
  }

  componentDidMount(x, y, z){
    const area = ReactDOM.findDOMNode(this),
          info = area.getElementsByClassName("ex-description-wrapper")[0];
    // areaRect = area.getBoundingClientRect(),
    if (info) {
      // HACK: для правильного определения размера в хроме функция вызывается с таймаутом
      setTimeout(() => {
        const infoRect = info.getBoundingClientRect(),
              window_width = window.innerWidth,
              width = 250, // todo: calculate width
              left = infoRect.right,
              h_pos = window_width < left + width ? "right" : "left";
          this.setState({h_pos});
      }, 10)
    }
  }

  getDescriptionBaloon(data, characteristics){
    let annotations = {};
    if (data.extra) {
      for (const [key, val] of Object.entries(data.extra)) {
        if (val instanceof Object && 'name' in val && 'value' in val)
          annotations[key] = val;
      }
    }

    if (characteristics.length) {
      return(
        <div className="ex-description-wrapper">
          <div className="ex-baloon">
            <div className="ex-arrow"></div>
            <ul className="ex-attrs">
              {characteristics.map(
                (child, i) =>
                  <li  className="characteristic"
                    data-path={child.path} key={i}
                    data-view-class={child.view_class.join(" ")}>
                    <strong>{child.name}:&nbsp;</strong>
                    {child.values.join("; ")}
                  </li>
              )}
              {Object.keys(annotations).map(
                (key, i) =>
                  <li className="annotation" key={i}
                    data-view-class={key}>
                    <strong>{annotations[key].name}:&nbsp;</strong>
                    {annotations[key].value.map(val => <span>{val};&nbsp;</span>)}
                  </li>
              )}
            </ul>
          </div>
        </div>
      );
    }
  }

  getItemContent(data, title, marks){
    const url = data.extra && data.extra.url ? data.extra.url : data.entity_url;
    return(
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
  }

  getItemBlock(descriptionBaloon, itemContent, groupDigit, groupSize){
    if (!groupSize){
      return (
        <div className="ex-catalog-item-block"
             onClickCapture={e => { ::this.handleMouseClick(e); } }>
          {descriptionBaloon}
          {itemContent}
        </div>
      )
    } else {
      return (
        <div className="ex-catalog-item-block ex-catalog-item-variants"
             onClickCapture={e => { ::this.handleMouseClick(e); } }>
          <div>
            <div>
              {descriptionBaloon}
              {groupDigit}
              {itemContent}
            </div>
          </div>
        </div>
      )
    }
  }
};

export default TileItemMixin