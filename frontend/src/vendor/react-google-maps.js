/*
 * Офлайн-заглушка пакета `react-google-maps`.
 *
 * Пакет объявлен в frontend/package.json, но отсутствует в предсобранном
 * офлайн-дереве зависимостей (/home/agent/workspace/venvs/edw-frontend/node_modules).
 * Сборочный скрипт frontend/scripts/build.mjs подставляет этот модуль только
 * тогда, когда настоящий пакет не найден; при установленных зависимостях
 * карты рендерятся настоящим react-google-maps, а этот файл не попадает в бандл.
 *
 * Заглушка повторяет сигнатуры, которые использует components/BaseEntities/Map.js,
 * и рендерит пустой контейнер той же высоты вместо интерактивной карты.
 */
import React from 'react';


// Map.js строит иконки маркеров через глобальный google.maps API стороннего
// скрипта. Без react-google-maps этот код не должен падать на отсутствии
// провайдера, поэтому глобальный объект дополняется минимально достаточными
// конструкторами (их результат только передаётся в свойства маркера).
function ensureGoogleMapsGlobal() {
  const scope = typeof globalThis !== 'undefined' ? globalThis : null;
  if (!scope)
    return;

  if (!scope.google)
    scope.google = {};
  if (!scope.google.maps)
    scope.google.maps = {};

  const maps = scope.google.maps;
  if (!maps.Size) {
    maps.Size = function Size(width, height) {
      this.width = width;
      this.height = height;
    };
  }
  if (!maps.Point) {
    maps.Point = function Point(x, y) {
      this.x = x;
      this.y = y;
    };
  }
  if (!maps.MarkerImage) {
    maps.MarkerImage = function MarkerImage(url, size, origin, anchor) {
      this.url = url;
      this.size = size;
      this.origin = origin;
      this.anchor = anchor;
    };
  }
  if (!maps.SymbolPath)
    maps.SymbolPath = {CIRCLE: 0};
}

ensureGoogleMapsGlobal();


function MapProviderUnavailable(props) {
  const container = props.containerElement;
  const style = container && container.props ? container.props.style : null;

  return React.createElement('div', {
    className: 'ex-map-provider-unavailable',
    'data-map-provider': 'react-google-maps',
    style: style || null,
  });
}


export function withGoogleMap() {
  return function GoogleMapContainer(props) {
    return React.createElement(MapProviderUnavailable, props);
  };
}


export function GoogleMap(props) {
  return React.createElement(MapProviderUnavailable, props);
}


export function Marker() {
  return null;
}


export function InfoWindow(props) {
  return React.createElement(React.Fragment, null, props.children || null);
}
