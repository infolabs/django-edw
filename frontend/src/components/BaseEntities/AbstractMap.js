import React, {Component} from 'react';
import ReactDOM from 'react-dom';
import marked from 'marked';


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

  state = {
    markers: [],
    itemsChanged: false
  };


  componentDidUpdate(prevProps, prevState) {
    const itemsChanged = this.props.items != prevProps.items;
    if (prevState.itemsChanged != itemsChanged) {
      this.setState({itemsChanged});
      return true
    }
    return false
  }


  componentDidMount(x, y, z) {
    this.setState({
      div: ReactDOM.findDOMNode(this)
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

  getPinColor(item) {
    let pinColor = "CECECE";
    const pinColorPattern = item.extra.group_size ? "group-pin-color-" : "pin-color-";
    if (item.short_marks.length) {
      for (const sm of item.short_marks) {
        if (sm.view_class.length) {
          for (const cl of sm.view_class) {
            if(cl.startsWith(pinColorPattern)) {
              pinColor = cl.replace(pinColorPattern, "").toUpperCase();
              return pinColor;
            }
          }
        }
      }
    }
    return pinColor;
  }

  handleInfoMouseClick(e, data) {
    const { actions, meta } = this.props;
    if (data.extra.group_size) {
      actions.notifyLoadingEntities();
      actions.expandGroup(data.id, meta);
    }
  }

  assembleInfo(item, meta, description) {
    const url = item.extra.url ? item.extra.url : item.entity_url,
          marks = description ? description.marks : item.short_marks || [],
          characteristics = description ? description.characteristics : item.short_characteristics || [];
    const title = item.extra.group_size && !meta.alike ? item.extra.group_name : item.entity_name;

    let media = item.media;

    let header = <a href={url}>{title}</a>;
    if (item.extra.group_size) {
        // strip links
        media = media.replace(/<a\b[^>]*>/i,"").replace(/<\/a>/i, "");
        header = title;
    }

    return (
      <div className="ex-map-info"
           onClick={e => {this.handleInfoMouseClick(e, item);}}
           style={item.extra.group_size && {cursor: 'pointer'}}>
        <div className="ex-map-img" dangerouslySetInnerHTML={{__html: marked(media, {sanitize: false})}} />

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

        <div className="ex-map-descr">
          <h5>{header}</h5>
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
      </div>
    );
  }

}