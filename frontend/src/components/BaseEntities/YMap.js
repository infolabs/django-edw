import React from 'react';
import ReactDOMServer from 'react-dom/server';
import { withYMaps, YMaps, Map, Placemark } from 'react-yandex-maps';

import AbstractMap from 'components/BaseEntities/AbstractMap';
import { MAP_HEIGHT } from 'constants/Components';


const defaultState = {
  bounds: [[50.1, 30.2],[60.3, 20.4]],
  margin: 50,
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
  'control.ZoomControl'
];

const markerModules = [
  'geoObject.addon.balloon',
];


class YMapInner extends AbstractMap {
  setMapRef = ref => { this._map = ref; };

  closeBalloon(e) {
    e.get('target').balloon.close();
  }

  handleMarkerClick(e1, data) {
    e1.get('target').balloon.events.add('click', e2 => {
      this.handleInfoMouseClick(e2, data);
    });
  }

  componentWillMount() {
    const style = `width: {{ options.diameter }}px;
                   height: {{ options.diameter }}px;
                   line-height: {{ options.diameter }}px;
                   left: {{ options.offset.0 }}px;
                   top: {{ options.offset.1 }}px;
                   position: relative;`;

    const circle = `
      <div style="${style}">
        <svg xmlns="http://www.w3.org/2000/svg"
             style="position: absolute;"
             width="100%" height="100%"
             viewBox="0 0 100 100">
           <circle cx="50" cy="50" r="40"
            stroke="#121212"
            stroke-width="1.5"
            fill="{{ options.color }}"
            vector-effect="non-scaling-stroke"/>
        </svg>
        <div style="position: absolute; height: 100%; width: 100%; text-align: center;">
            {{ properties.iconContent }}
        </div>
      </div>
    `;

    this.circleLayout = this.props.ymaps.templateLayoutFactory.createClass(circle);
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

      let marker = {
        center: [lat, lng],
        properties: {
          balloonContent: balloonContent
        },
        item: item
      };

      if (item.extra && item.extra.group_size) {
        const label = item.extra.group_size.toString();
        const diameter = 17 + label.length * 12;
        const radius = diameter / 2;
        marker.properties.iconContent = label;
        marker.options = {
          preset: {iconLayout: this.circleLayout},
          iconColor: 'white',
          iconDiameter: diameter,
          iconOffset: [-radius / 2, -radius / 2],
          iconShape: {
            type: 'Circle',
            coordinates: [radius / 2, radius / 2],
            radius: radius
          },
          hideIconOnBalloonOpen: false
        };
      } else {
        marker.options = {
          preset: 'islands#dotIcon',
          iconColor: '#' + pinColor,
          hideIconOnBalloonOpen: false
        };
      }

      markers.push(marker);
    }

    let mapState = defaultState;

    if ((!geoItems.length || !this.state.itemsChanged) && this._map) {
      mapState.bounds = this._map.getBounds();
    } else {
      mapState.bounds = [[latMin, lngMin],[latMax, lngMax]];
    }

    // explicitly update map
    if (this.state.itemsChanged && this._map) {
      this._map.setBounds(mapState.bounds, {checkZoomRange: true});
    }

    return (
      <div className={entitiesClass}>
        <Map style={{ height: MAP_HEIGHT }}
             state={mapState}
             options={{suppressMapOpenBlock: true}}
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
    );
  }
}


const YMapWrapped = withYMaps(YMapInner, true, ['templateLayoutFactory']);


export default class YMap extends React.Component {
  render() {
    return (
      <YMaps>
        <YMapWrapped {...this.props} />
      </YMaps>
    );
  }
}

