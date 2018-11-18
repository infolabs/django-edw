import React from 'react';
import ReactDOMServer from 'react-dom/server';
import { YMaps, Map, Placemark } from 'react-yandex-maps';

import AbstractMap from 'components/BaseEntities/AbstractMap';
import { MAP_HEIGHT } from 'constants/Components';


const defaultState = {
  center: [55.76, 37.64],
  zoom: 15,
  type: 'yandex#map',
  controls: [
    'fullscreenControl',
    'geolocationControl',
    'zoomControl',
  ],
  behaviors: [
    'drag',
    'dblClickZoom',
    'rightMouseButtonMagnifier',
    'multiTouch'
  ]
};

const mapModules = [
  'control.FullscreenControl',
  'control.GeolocationControl',
  'control.ZoomControl',
];

const markerModules = [
  'geoObject.addon.balloon'
];


export default class YMap extends AbstractMap {
  setMapRef = ref => { this._map = ref; };

  closeBalloon(e) {
    e.get('target').balloon.close();
  }

  handleMarkerClick(e1, data) {
    e1.get('target').balloon.events.add('click', e2 => {
      this.handleInfoMouseClick(e2, data);
    });
  }

  render() {
    const { items, meta, loading } = this.props;
    const geoItems = items.filter(item => !!(item.extra && item.extra.geoposition));

    let entitiesClass = "entities";
    entitiesClass = loading ? entitiesClass + " ex-state-loading" : entitiesClass;

    let lngMin, latMin, lngMax, latMax, markers = [];

    for (const item of geoItems) {
      const coords = item.extra.geoposition.split(','),
            lng = parseFloat(coords[1]),
            lat = parseFloat(coords[0]);
      lngMin = lngMin != null && lngMin < lng ? lngMin : lng;
      lngMax = lngMax != null && lngMax > lng ? lngMax : lng;
      latMin = latMin != null && latMin < lat ? latMin : lat;
      latMax = latMax != null && latMax > lat ? latMax : lat;


      const pinColor = this.getPinColor(item),
            info = this.assembleInfo(item, meta),
            balloonContent = ReactDOMServer.renderToString(info);

      const marker = {
        center: [lat, lng],
        properties: {
          balloonContent: balloonContent
        },
        options: {
          preset: 'islands#dotIcon',
          iconColor: '#' + pinColor,
          hideIconOnBalloonOpen: false
        },
        item: item
      };
      if (item.extra.group_size) {
        marker.properties.iconContent = item.extra.group_size.toString();
        marker.options.preset = 'islands#icon';
      }
      markers.push(marker);
    }

    let center, zoom;

    if ((!geoItems.length || !this.state.itemsChanged) && this._map) {
      zoom = this._map.getZoom();
      center = this._map.getCenter();
    } else {
      zoom = this.calculateZoom(lngMin, lngMax, latMin, latMax);
      const latMap = latMin + (latMax - latMin) / 2,
            lngMap = lngMin + (lngMax - lngMin) / 2;
      center = [latMap, lngMap];
    }

    if (!zoom && !geoItems.length)
      return null;

    const mapState = Object.assign({}, defaultState, {zoom, center});

    return (
      <YMaps>
        <div className={entitiesClass}>
          <Map style={{ height: MAP_HEIGHT }}
               state={mapState}
               modules={mapModules}
               instanceRef={this.setMapRef}>
            {markers.map(
              (marker, i) => 
              <Placemark key={i}
                         modules={markerModules}
                         geometry={marker.center}
                         properties={marker.properties}
                         options={marker.options}
                         onGeometrychange={this.closeBalloon}
                         onBalloonopen={e => this.handleMarkerClick(e, marker.item)}/>
            )}
          </Map>
        </div>
      </YMaps>
    );
  }
}
