import React from 'react';
import {
  withGoogleMap,
  GoogleMap,
  Marker,
  InfoWindow
} from "react-google-maps";
import AbstractMap from 'components/BaseEntities/AbstractMap';
import { MAP_HEIGHT } from 'constants/Components';


// Map component
// <script src="https://maps.googleapis.com/maps/api/js"></script>


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


export default class Map extends AbstractMap {
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
    let pinImage = new google.maps.MarkerImage("https://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|" + pinColor,
      new google.maps.Size(21, 34),
      new google.maps.Point(0,0),
      new google.maps.Point(10, 34)
    );
    return pinImage;
  }

  getGroupMarkerIcon(label, pinColor = "FE7569") {
    let pinImage = {
      path: google.maps.SymbolPath.CIRCLE,
      scale: 9 + label.length * 4,
      fillColor: "#" + pinColor,
      fillOpacity: 1.0,
      strokeWeight: 1.5,
    };
    return pinImage;
  }

  getMarkerShadow() {
    let pinShadow = new google.maps.MarkerImage("https://chart.apis.google.com/chart?chst=d_map_pin_shadow",
      new google.maps.Size(40, 37),
      new google.maps.Point(0, 0),
      new google.maps.Point(12, 35)
    );
    return pinShadow;
  }

  componentDidUpdate(prevProps) {
    super.componentDidUpdate(prevProps);
    if (this.state.markers.length)
      this.setState({markers: []});
  }

  handleMapMounted(map) {
    this._map = map;
  }

  render() {
    const { items, loading, meta } = this.props;

    let entities_class = "entities";
    entities_class = loading ? entities_class + " ex-state-loading" : entities_class;

    const geo_items = items.filter(item => !!(item.extra && item.extra.geoposition));

    let min_lng = null,
        min_lat = null,
        max_lng = null,
        max_lat = null,
        markers = this.state.markers;

    for (const item of geo_items) {
      const coords = item.extra.geoposition.split(','),
            lng = parseFloat(coords[1]),
            lat = parseFloat(coords[0]);
      min_lng = min_lng != null && min_lng < lng ? min_lng : lng;
      max_lng = max_lng != null && max_lng > lng ? max_lng : lng;
      min_lat = min_lat != null && min_lat < lat ? min_lat : lat;
      max_lat = max_lat != null && max_lat > lat ? max_lat : lat;

      let pinColor = this.getPinColor(item);

      let marker = {
          position: {lat: lat, lng: lng},
          info: this.assembleInfo(item, meta)
      };

      if (item.extra && item.extra.group_size) {
        const label = item.extra.group_size.toString();
        marker["icon"] = this.getGroupMarkerIcon(label, pinColor);
        marker["label"] = label;
      } else {
        marker["icon"] = this.getMarkerIcon(pinColor);
        marker["shadow"] = this.getMarkerShadow();
      }

      markers.push(marker);
    }

    let map_lng = min_lng + (max_lng - min_lng) / 2,
        map_lat = min_lat + (max_lat - min_lat) / 2,
        zoom = this.calculateZoom(min_lng, max_lng, min_lat, max_lat);

    if ((!geo_items.length || !this.state.itemsChanged) && this._map) {
      zoom = this._map.getZoom();
      const center = this._map.getCenter();
      map_lat = center.lat();
      map_lng = center.lng();
    }

    if (!zoom && !geo_items.length)
      return null;

    return (
      <div className={entities_class}>
        <ProblemMap markers={markers}
                    lng={map_lng}
                    lat={map_lat}
                    zoom={zoom}
                    containerElement={
                      <div style={{ height: MAP_HEIGHT }} />
                    }
                    mapElement={
                      <div style={{ height: MAP_HEIGHT }} />
                    }
                    onMarkerClick={this.handleMarkerClick}
                    onMarkerClose={this.handleMarkerClose}
                    onMapMounted={this.handleMapMounted}
        />
      </div>
    );
  }
}
