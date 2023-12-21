import React from 'react';
import ReactDOM from 'react-dom';
import marked from 'marked';


const TOGGLE_DESCRIPTION_DELAY = 100;

const ListItemMixin = Base => class extends Base {

  constructor(){
    super();
    this.state = {
      minHeight: 0,
      isHover: false,
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
    if (data.extra && data.extra.group_size) {
      actions.notifyLoadingEntities();
      actions.expandGroup(data.id, meta);
      e.preventDefault();
      e.stopPropagation();
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.props.loading !== prevProps.loading)
      this.setState({minHeight: 'auto'});
  }

  toggleDescription(e) {
    const { data, meta, actions, descriptions } = this.props,
          id = data.id,
          lastIsHover = this.getIsHover(e.clientX, e.clientY);

    this.setState({isHover: lastIsHover});

    let context = this;
    setTimeout(function() {
      const { isHover } = context.state;

      if (lastIsHover === isHover) {
        if (isHover) {
          try {
            const area = ReactDOM.findDOMNode(context),
                  areaRect = area.getBoundingClientRect();
            context.setState({minHeight: areaRect.height});
          } catch (err) {
            // pass
          }

          actions.showDescription(id);

          if ((data.extra && data.extra.group_size) && !meta.alike && !descriptions.groups[id])
            actions.getEntityInfo(data, meta);

          if ((data.extra && !data.extra.group_size) && !descriptions[id])
            actions.getEntityInfo(data);

        } else {
          context.setState({minHeight: 'auto'});
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

  getExAttrs(data, characteristics){
    let annotations = {};
    if (data.extra) {
      for (const [key, val] of Object.entries(data.extra)) {
        if (val instanceof Object && 'name' in val && 'value' in val)
          annotations[key] = val;
      }
    }

    return (
      <ul className="ex-attrs">
        {Object.keys(annotations).length !== 0 &&
          <li className="annotation">
            {Object.keys(annotations).map(
              (key, i) =>
              annotations[key].value != null ?
                <div key={i}>
                    <strong>{annotations[key].name}:&nbsp;</strong>
                    {annotations[key].value instanceof Array ?
                      annotations[key].value.map((val, k) => <span key={k}>{val};&nbsp;</span>)
                    :
                      <span key={key}>{annotations[key].value}</span>
                    }
                  </div> :
                  ''
            )}
          </li>
        }
        {characteristics.map(
          (child, i) =>
            <li data-path={child.path} key={i}
              data-view-class={child.view_class.join(' ')}>
              <strong>{child.name}:&nbsp;</strong>
              {child.values.join('; ')}
            </li>
        )}
      </ul>
    );
  }

  getExTags(marks){
    return (
      <ul className="ex-tags">
        {marks.map(
          (child, i) =>
            <li className="ex-tag"
                key={i}
                data-name={child.name}
                data-path={child.path}
                data-view-class={child.view_class.join(' ')}>
              <i className="fa fa-tag"/>&nbsp;
              {child.values.join(', ')}
            </li>
        )}
      </ul>
    );
  }

  getDescriptionBaloon(data, characteristics, marks, descriptions, exAttrs,exTags){
    if (characteristics.length) {
      return (
        <div className="ex-description-wrapper">
          {exAttrs}
          {descriptions.opened[data.id] && exTags}
        </div>
      );
    }
  }

  getItemBlock(url, data, title, descriptionBaloon){
    return (
      <div className="wrap-list-item__description">
        <a href={url}>
          <h4>{title}</h4>
        </a>
        {descriptionBaloon}
      </div>
    );
  }

  getItemContent(url, data, itemBlock, marks, wrapperClassName = 'wrap-list-item') {
    return (
      <div className={wrapperClassName}
           onClickCapture={e => { ::this.handleMouseClick(e); } }>
        <div className="row wrap-list-item__content">
          <div className="wrap-list-item__image">
            <div className="ex-media" dangerouslySetInnerHTML={{__html: marked(data.media, {sanitize: false})}}/>
          </div>
          {itemBlock}
        </div>

        <ul className="ex-ribbons">
          {marks.map(
            (child, i) =>
              <li className="ex-wrap-ribbon"
                  key={i}
                  data-name={child.name}
                  data-path={child.path}
                  data-view-class={child.view_class.join(' ')}>
                <div className="ex-ribbon">{child.values.join(', ')}</div>
              </li>
          )}
        </ul>
      </div>
    );
  }
};


export default ListItemMixin;
