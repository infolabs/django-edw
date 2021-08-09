import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import marked from 'marked';
import Color from 'color';


function latRad(lat) {
  let sin = Math.sin(lat * Math.PI / 180);
  let radX2 = Math.log((1 + sin) / (1 - sin)) / 2;
  return Math.max(Math.min(radX2, Math.PI), -Math.PI) / 2;
}


function zoom(mapPx, worldPx, fraction) {
  return Math.floor(Math.log(mapPx / worldPx / fraction) / Math.LN2);
}


export default class AbstractMap extends Component {
  _map = null;
  _DO_CLICK_ON_BALLOON = true;

  state = {
    markers: [],
    itemsChanged: false,
  };

  componentDidUpdate(prevProps, prevState) {
    const itemsChanged = this.props.items !== prevProps.items;
    if (prevState.itemsChanged !== itemsChanged)
      this.setState({itemsChanged});
  }

  componentDidMount(x, y, z) {
    this.setState({
      div: ReactDOM.findDOMNode(this),
    });
  }

  calculateZoom(west, east, south, north) {
    let width = 600,
        height = 400;

    const div = this.state.div;
    if (div) {
      width = div.clientWidth;
      height = div.clientHeight;
    }

    const WORLD_DIM = { height: 256, width: 256 },
          ZOOM_MAX = 16;

    const latFraction = (latRad(north) - latRad(south)) / Math.PI,
          lngDiff = east - west,
          lngFraction = ((lngDiff < 0) ? (lngDiff + 360) : lngDiff) / 360,
          latZoom = zoom(height, WORLD_DIM.height, latFraction),
          lngZoom = zoom(width, WORLD_DIM.width, lngFraction);

    return Math.min(latZoom, lngZoom, ZOOM_MAX);
  }

  getColorFromMarks(item, pattern) {
    for (const sm of item.short_marks) {
      for (const cl of sm.view_class) {
        if (cl.startsWith(pattern)) {
          const color = cl.replace(pattern, '').toUpperCase();
          return `#${color}`;
        }
      }
    }
    return null
  }

  _getPinColor(item) {
    return this.getColorFromMarks(item, 'pin-color-') || '#CECECE';
  }

  getPinColor(item) {
    return this._getPinColor(item);
  }

  _getGroupColor(item) {
    const color = this.getColorFromMarks(item, 'group-pin-color-');
    const regionColor = 'rgba(0,0,0,0)';
    let backgroundColorContent, borderColor;

    if (color) {
      backgroundColorContent = color;
      borderColor = Color(color).darken(0.5);
    } else {
      backgroundColorContent = 'white';
      borderColor = 'black';
    }
    return {backgroundColorContent, borderColor, regionColor};
  }

  getGroupColor(item) {
    return this._getGroupColor(item);
  }

  convertSnakeToCamelCase(str) {
    const words = str.split('_');
    for (let i = 1; i < words.length; i++) {
      words[i] = words[i].charAt(0).toUpperCase() + words[i].slice(1);
    }
    return words.join('');
  }

  _getPinPreset(item) {
    let pinPreset = 'islands#blueDotIcon';
    const presetPattern = 'yandex-preset-';
    for (const sm of item.short_marks) {
      for (const cl of sm.view_class) {
        if (cl.startsWith(presetPattern)) {
          pinPreset = cl.replace(presetPattern, '');
          return this.convertSnakeToCamelCase(pinPreset);
        }
      }
    }
    return pinPreset;
  }

  getPinPreset(item){
    return this._getPinPreset(item);
  }

  handleInfoMouseClick(e, data) {
    if (!this._DO_CLICK_ON_BALLOON)
      return;

    const { actions, meta } = this.props;
    if (data.extra.group_size) {
      actions.notifyLoadingEntities();
      actions.expandGroup(data.id, meta);
    }
  }


  assembleInfoVars(item, meta, description) {
    const url = item.extra.url ? item.extra.url : item.entity_url,
          marks = description ? description.marks : item.short_marks || [],
          characteristics = description ? description.characteristics : item.short_characteristics || [];
    const title = item.extra.group_size && !meta.alike ? item.extra.group_name : item.entity_name;

    let media = item.media;

    let header = <a href={url}>{title}</a>;
    if (item.extra.group_size) {
        // strip links
        media = media.replace(/<a\b[^>]*>/i, '').replace(/<\/a>/i, '');
        header = title;
    }
    return { marks, characteristics, media, header };
  }

  exRibbons(marks){
    return (
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
    );
  }

  exAttrs(characteristics, extra){
    let annotations = {};
    if (extra) {
      for (const [key, val] of Object.entries(extra)) {
        if (val instanceof Object && 'name' in val && 'value' in val)
          annotations[key] = val;
      }
    }

    return (
      <ul className="ex-attrs">
        {characteristics.map(
          (child, i) =>
            child.values.length < 5 ?
            <li data-path={child.path} key={i}
                data-view-class={child.view_class.join(' ')}>
              <strong>{child.name}:</strong>&nbsp;
              {child.values.join('; ')}
            </li>
                :
            <li data-path={child.path} key={i}
                data-view-class={child.view_class.join(' ')}>
              <strong>{child.name}:</strong>&nbsp;
              {child.values.join('; ').split('; ',5).join('; ')}...
            </li>
        )}
        {Object.keys(annotations).map(
          (key, i) =>
            <li className="annotation" key={i}
              data-view-class={key}>
              <strong>{annotations[key].name}:&nbsp;</strong>
              {annotations[key].value instanceof Array ?
                annotations[key].value.map((val, k) => <span key={k}>{val};&nbsp;</span>)
              :
                <span key={key}>{annotations[key].value}</span>
              }
            </li>
        )}
      </ul>
    );
  }

  exTags(marks){
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

  assembleInfo(item, meta, description) {
    const { marks, characteristics, media, header } = this.assembleInfoVars(item, meta, description),
          exRibbons = this.exRibbons(marks),
          exAttrs = this.exAttrs(characteristics, item.extra),
          exTags = this.exTags(marks);

    return (
      <div className={item.extra.group_size ? 'ex-map-info ex-catalog-item-variants' :
          'ex-map-info'}
           style={item.extra.group_size && {cursor: 'pointer'}}>
        <div className="ex-map-img" dangerouslySetInnerHTML={{__html: marked(media, {sanitize: false})}} />
        {exRibbons}
        <div className="ex-map-descr">
          <h5>{header}</h5>
          {exAttrs}
          {exTags}
        </div>
      </div>
    );
  }
}
