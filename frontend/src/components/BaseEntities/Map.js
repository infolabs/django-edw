import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import  marked from 'marked';
import { withGoogleMap, GoogleMap, Marker, InfoWindow } from "react-google-maps";

// Map component
// <script src="https://maps.googleapis.com/maps/api/js"></script>

function latRad(lat) {
  let sin = Math.sin(lat * Math.PI / 180);
  let radX2 = Math.log((1 + sin) / (1 - sin)) / 2;
  return Math.max(Math.min(radX2, Math.PI), -Math.PI) / 2;
}

function zoom(mapPx, worldPx, fraction) {
  return Math.floor(Math.log(mapPx / worldPx / fraction) / Math.LN2);
}

const ProblemMap = withGoogleMap(props => (
  <GoogleMap
    ref={props.onMapMounted}
    zoom={props.zoom}
    center={{ lat: props.lat, lng: props.lng }}
    defaultOptions={{ streetViewControl: false, scrollwheel: false }}
  >
    {props.markers.map((marker, key) => (
      <Marker {...marker}
              key={key}
              onClick={() => props.onMarkerClick(marker)}
      >
        {marker.showInfo && (
          <InfoWindow onCloseClick={() => props.onMarkerClose(marker)}>
            <div>{marker.info}</div>
          </InfoWindow>
        )}
      </Marker>
    ))}
  </GoogleMap>
));

export default class Map extends Component {
  state = {
    markers: []
  }

  handleMarkerClick = this.handleMarkerClick.bind(this);
  handleMarkerClose = this.handleMarkerClose.bind(this);
  handleMapMounted = this.handleMapMounted.bind(this);

  handleMarkerClick(targetMarker) {
    this.setState({
      markers: this.state.markers.map(marker => {
        let showInfo = false;
        if (marker === targetMarker) {
          showInfo = true;
        }
        return {
          ...marker,
          showInfo: showInfo,
        };
      }),
    });
  }

  handleMarkerClose(targetMarker) {
    this.setState({
      markers: this.state.markers.map(marker => {
        if (marker === targetMarker) {
          return {
            ...marker,
            showInfo: false,
          };
        }
        return marker;
      }),
    });
  }

  getMarkerIcon(pinColor = "FE7569") {
    let pinImage = new google.maps.MarkerImage("http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|" + pinColor,
      new google.maps.Size(21, 34),
      new google.maps.Point(0,0),
      new google.maps.Point(10, 34)
    );
    return pinImage;
  }

  getMarkerShadow() {
    let pinShadow = new google.maps.MarkerImage("http://chart.apis.google.com/chart?chst=d_map_pin_shadow",
      new google.maps.Size(40, 37),
      new google.maps.Point(0, 0),
      new google.maps.Point(12, 35)
    );
    return pinShadow;
  }

  componentWillReceiveProps(nextProps) {
    this.setState({
      markers: []
    });
  }

  componentDidMount(x, y, z) {
    this.setState({
      div: ReactDOM.findDOMNode(this)
    });
  }

  handleMapMounted(map) {
    this._map = map;
  }

  calculateZoom(west, east, south, north) {

    const div = this.state.div;
    let width = 600,
        height = 400;

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
    let pinColor = "FE7569";
    if (item.short_marks.length) {
      for (const sm of item.short_marks) {
        if (sm.view_class.length) {
          for (const cl of sm.view_class) {
            if(cl.startsWith("pin-color-")) {
              pinColor = cl.replace("pin-color-", "").toUpperCase();
              return pinColor;
            }
          }
        }
      }
    }
    return pinColor;
  }

  render() {
    const { items, actions, loading, descriptions } = this.props;
    let entities_class = "entities";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    const geo_items = items.filter(item => !!(item.extra && item.extra.geoposition));

    let min_lng = null,
        min_lat = null,
        max_lng = null,
        max_lat = null,
        markers = this.state.markers,
        old_markers = this.state.markers.length,
        shadow = this.getMarkerShadow();

    for (const item of geo_items) {
      const coords = item.extra.geoposition.split(','),
            lng = parseFloat(coords[1]),
            lat = parseFloat(coords[0]);
      min_lng = min_lng != null && min_lng < lng ? min_lng : lng;
      max_lng = max_lng != null && max_lng > lng ? max_lng : lng;
      min_lat = min_lat != null && min_lat < lat ? min_lat : lat;
      max_lat = max_lat != null && max_lat > lat ? max_lat : lat;

      let pinColor = this.getPinColor(item);

      const url = item.extra.url ? item.extra.url : itemdata.entity_url,
            marks = item.short_marks || [];

      const info = (
        <div className="ex-map-info">
          <div className="ex-map-img" dangerouslySetInnerHTML={{__html: marked(item.media, {sanitize: false})}} />

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
            <h5><a href={url}>{item.entity_name}</a></h5>
            <ul className="ex-attrs">
              {item.short_characteristics.map(
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

      markers.push(
        {
          position: {lat: lat, lng: lng},
          info: info,
          icon: this.getMarkerIcon(pinColor),
          shadow: shadow
        }
      );
    }

    let map_lng = min_lng + (max_lng - min_lng) / 2,
        map_lat = min_lat + (max_lat - min_lat) / 2,
        zoom = this.calculateZoom(min_lng, max_lng, min_lat, max_lat);

    if ((!geo_items.length || old_markers) && this._map) {
      zoom = this._map.getZoom();
      const center = this._map.getCenter();
      map_lat = center.lat();
      map_lng = center.lng();
    }

    if (!zoom && !geo_items.length)
      return <div></div>;

    return (
      <div className={entities_class}>
        <ProblemMap markers={markers}
                    lng={map_lng}
                    lat={map_lat}
                    zoom={zoom}
                    containerElement={
                      <div style={{ height: '400px' }} />
                    }
                    mapElement={
                      <div style={{ height: '400px' }} />
                    }
                    onMarkerClick={this.handleMarkerClick}
                    onMarkerClose={this.handleMarkerClose}
                    onMapMounted={this.handleMapMounted}
        />
      </div>
    );
  }
}
