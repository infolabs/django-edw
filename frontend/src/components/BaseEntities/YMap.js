import React from 'react';
import ReactDOMServer from 'react-dom/server';
import { withYMaps, YMaps, Map, Placemark } from 'react-yandex-maps';

import AbstractMap from 'components/BaseEntities/AbstractMap';
import { MAP_HEIGHT } from 'constants/Components';

// import `color` lib
const Color = require('color');

export const defaultState = {
  bounds: [[50.1, 30.2], [60.3, 20.4]],
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

export const mapModules = [
  'control.FullscreenControl',
  'control.GeolocationControl',
  'control.ZoomControl'
];

export const markerModules = [
  'geoObject.addon.balloon',
];

export function addRegions(map, osmArray, osmRegion) {
    for (const osm of osmArray) {
        osmeRegions.geoJSON(osm.osmId, {
            lang: 'ru',
            quality: 3,
            postFilter: function(region){
                return region.osmId == osm.osmId;
            }
        }, (data) => {
            let collection = osmeRegions.toYandex(data, ymaps);
            collection.add(map);
            osm._collection = collection;
            collection.setStyles(() => {
                return getRegionsStyle(osm, osmRegion)
            });
        });
    }
}

function getRegionsStyle(osm, osmRegion){
  switch (osmRegion){
    case 'avg':
      const nm = osm.colors.length;
      if(nm > 1){
        let [r, g, b] = [0, 0, 0];
        osm.colors.map((array, i) => {
          const color = Color(array).rgb().array();
          r += color[0];
          g += color[1];
          b += color[2];
        });
        osm.colors = `rgba(${Math.round(r/nm)}, ${Math.round(g/nm)}, ${Math.round(b/nm)}, 0.08)`;
      } else {
        osm.colors = osm.colors[0];
      }
      break;
    default :
      osm.colors = osm.colors[0];
  }
  return ({
      strokeWidth: 1,
      strokeStyle: "longdashdotdot",
      strokeColor: "#5CA5C1",
      fillColor: osm.colors
  });
}


export class YMapInner extends AbstractMap {

  setMapRef = ref => {
      this._map = ref;
      if(ref && !this.firstMapLoading && this.osmRegion){
          this.firstMapLoading = true; // Флаг загрузки региона при инициализации карты
          addRegions(this._map, this.osmArray, this.osmRegion);
          this.osmArrayPrev = this.osmArray;
      }
  };

  // Пока не нужен, см todo ниже
  // onGeometryChange(e) {
  //   e.get('target').balloon.close();
  // }

  handleBalloonOpen(e1, marker) {
    const { actions, meta, descriptions } = this.props,
          data = marker.item,
          id = data.id;

    e1.get('target').balloon.events.add('click', e2 => {
      this.handleInfoMouseClick(e2, data);
    });

    if (data.extra.group_size && !meta.alike && !descriptions.groups[id])
      actions.getEntityItem(data, meta);

    if (!data.extra.group_size && !descriptions[id])
      actions.getEntityItem(data);

    actions.showDescription(id);
  }

  handleBalloonClose(e1, marker) {
    const { actions } = this.props;
    actions.hideDescription(marker.item.id);
  }

  componentDidMount() {
    this.osmRegion = this.props.data_mart.osm_region || null;

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
            stroke="{{ options.stroke }}"
            stroke-width="1.5"
            fill="{{ options.color }}"
            vector-effect="non-scaling-stroke"/>
        </svg>
        <div style="position: absolute; height: 100%; width: 100%; text-align: center;">
            {{ properties.iconContent }}
        </div>
      </div>
    `;

    this.setState({
      circleLayout: this.props.ymaps.templateLayoutFactory.createClass(circle)
    });
  }

  adjustBounds(lng, lat, lngMin, lngMax, latMin, latMax) {
    lngMin = lngMin != null && lngMin < lng ? lngMin : lng;
    lngMax = lngMax != null && lngMax > lng ? lngMax : lng;
    latMin = latMin != null && latMin < lat ? latMin : lat;
    latMax = latMax != null && latMax > lat ? latMax : lat;
    return { lngMin, lngMax, latMin, latMax };
  }

  render() {
    const { items, meta, loading, descriptions } = this.props,
          geoItems = items.filter(item => !!(item.extra && item.extra.geoposition));

    let entitiesClass = "entities";
    entitiesClass = loading ? entitiesClass + " ex-state-loading" : entitiesClass;

    let lngMin = null, latMin = null, lngMax = null, latMax = null, markers = [];

    this.osmArray = [];
    const osmAddrPattern = "osm-id-";
    let osmId;

    for (const item of geoItems) {

      const shortCharacteristics = item.short_characteristics[0].view_class,
            coords = item.extra.geoposition.split(','),
            lng = parseFloat(coords[1]),
            lat = parseFloat(coords[0]);

      ({ lngMin, lngMax, latMin, latMax } = this.adjustBounds(lng, lat, lngMin, lngMax, latMin, latMax));

      const colorItems = this.getColor(item),
            groupColor = colorItems.backgroundColorContent,
            borderGroupColor = colorItems.borderColor,
            pinColor = this.getPinColor(item),
            regionColor = colorItems.regionColor,
            descriptions_data = item.extra && item.extra.group_size ? descriptions.groups : descriptions,
            description = !descriptions_data[item.id] && descriptions.groups ? descriptions.groups[item.id] : descriptions_data[item.id],
            info = this.assembleInfo(item, meta, description),
            balloonContent = ReactDOMServer.renderToString(info);

      let osmObj = {
            osmId : "",
            colors : []
          };

      if (item.short_characteristics.length) {
        for (const sm of item.short_characteristics) {
          if (sm.view_class.length) {
            for (const cl of sm.view_class) {
              if(cl.startsWith(osmAddrPattern)) {
                osmId = parseInt(cl.replace(osmAddrPattern, ""));
                break
              }
            }
          }
        }
      }

      if (!this.osmArray.some(osm => osm.osmId == osmId)){
        osmObj.osmId = osmId;
        osmObj.colors.push(regionColor);
        this.osmArray.push(osmObj);
      } else {
        this.osmArray[0].colors.push(regionColor);
      }

      let marker = {
        center: [lat, lng],
        properties: {
          balloonContent: balloonContent
        },
        item: item
      };

      marker.prefix = '';

      if (item.extra && item.extra.group_size) {
        marker.prefix = 'group-';
        const label = item.extra.group_size.toString(),
              diameter = 17 + label.length * 12,
              radius = diameter / 2;
        marker.properties.iconContent = label;
        marker.options = {
          preset: {iconLayout: this.state.circleLayout},
          iconColor: groupColor,
          iconStroke: borderGroupColor,
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
    } else if (geoItems.length == 1) {
      // expand collapsed bounds to a square
      const dl = 0.0005;
      mapState.bounds = [[latMin - dl, lngMin - dl], [latMax + dl, lngMax + dl]];
    } else if (lngMin != null && latMin != null && lngMax != null && latMax != null) {
      const dl = Math.min(0.054 * Math.pow(latMax - latMin, 2), 0.1);
      mapState.bounds = [[latMin + dl, lngMin], [latMax, lngMax]];
    } else {
      mapState.bounds = defaultState.bounds;
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
            <Placemark key={marker.prefix + marker.item.id}
                       modules={markerModules}
                       defaultGeometry={marker.center}
                       properties={marker.properties}
                       defaultOptions={marker.options}
                       onBalloonopen={e => this.handleBalloonOpen(e, marker)}
                       onBalloonclose={e => this.handleBalloonClose(e, marker)}
                       // todo: Работает даже просто при перерендере карты при загрузке данных,
                       //       надо придумать другой механизм закрытия всплывашек при изменении размеров окна.
                       // onGeometrychange={this.onGeometryChange}
            />

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

