/*
 * Офлайн-заглушка пакета `react-yandex-maps`.
 *
 * Пакет объявлен в frontend/package.json, но отсутствует в предсобранном
 * офлайн-дереве зависимостей (/home/agent/workspace/venvs/edw-frontend/node_modules).
 * Сборочный скрипт frontend/scripts/build.mjs подставляет этот модуль только
 * тогда, когда настоящий пакет не найден; при установленных зависимостях
 * карты рендерятся настоящим react-yandex-maps, а этот файл не попадает в бандл.
 *
 * Заглушка повторяет сигнатуры, которые использует components/BaseEntities/YMap.js,
 * и рендерит пустой контейнер той же высоты вместо интерактивной карты.
 */
import React from 'react';


// YMapInner в componentDidMount обращается к this.props.ymaps (API Яндекс.Карт
// вставляет его withYMaps). Заглушка передаёт минимально достаточный объект,
// чтобы деградация до пустого контейнера не ломала остальную витрину.
const ymapsStub = {
  templateLayoutFactory: {
    createClass: (content) => function layout() {
      return content;
    },
  },
};


function MapProviderUnavailable(props) {
  return React.createElement('div', {
    className: 'ex-map-provider-unavailable',
    'data-map-provider': 'react-yandex-maps',
    style: props.style || null,
  }, props.children || null);
}


export function withYMaps(Component) {
  return function YMapsContainer(props) {
    return React.createElement(Component, Object.assign({}, props, {ymaps: ymapsStub}));
  };
}


export function YMaps(props) {
  return React.createElement(React.Fragment, null, props.children || null);
}


export function Map(props) {
  return React.createElement(MapProviderUnavailable, props);
}


export function Placemark() {
  return null;
}
