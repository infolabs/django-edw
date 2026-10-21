/*
 * Офлайн-замена пакета `color` (MIT, Qix-).
 *
 * Пакет объявлен в frontend/package.json, но отсутствует в предсобранном
 * офлайн-дереве зависимостей (/home/agent/workspace/venvs/edw-frontend/node_modules).
 * Сборочный скрипт frontend/scripts/build.mjs подставляет этот модуль только
 * тогда, когда настоящий пакет не найден; при установленных зависимостях
 * используется оригинальный `color`.
 *
 * Реализован ровно тот срез API, который нужен EDW:
 *   Color(hex | 'rgb(...)' | 'rgba(...)').rgb().array()
 *   Color(...).darken(ratio) -> css-строка
 */

const HEX_SHORT = /^#([0-9a-f])([0-9a-f])([0-9a-f])$/i;
const HEX_LONG = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?$/i;
const RGB_FUNC = /^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)$/i;


function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}


function parse(value) {
  if (typeof value !== 'string')
    throw new TypeError(`Unsupported color value: ${String(value)}`);

  const text = value.trim();

  let match = HEX_SHORT.exec(text);
  if (match)
    return {
      r: parseInt(match[1] + match[1], 16),
      g: parseInt(match[2] + match[2], 16),
      b: parseInt(match[3] + match[3], 16),
      a: 1,
    };

  match = HEX_LONG.exec(text);
  if (match)
    return {
      r: parseInt(match[1], 16),
      g: parseInt(match[2], 16),
      b: parseInt(match[3], 16),
      a: match[4] ? parseInt(match[4], 16) / 255 : 1,
    };

  match = RGB_FUNC.exec(text);
  if (match)
    return {
      r: parseFloat(match[1]),
      g: parseFloat(match[2]),
      b: parseFloat(match[3]),
      a: match[4] !== undefined ? parseFloat(match[4]) : 1,
    };

  throw new Error(`Unsupported color value: ${text}`);
}


function rgbToHsl({r, g, b}) {
  const rn = r / 255, gn = g / 255, bn = b / 255,
        max = Math.max(rn, gn, bn), min = Math.min(rn, gn, bn),
        delta = max - min,
        l = (max + min) / 2;

  let h = 0, s = 0;
  if (delta !== 0) {
    s = delta / (1 - Math.abs(2 * l - 1));
    if (max === rn)
      h = ((gn - bn) / delta) % 6;
    else if (max === gn)
      h = (bn - rn) / delta + 2;
    else
      h = (rn - gn) / delta + 4;
    h *= 60;
    if (h < 0)
      h += 360;
  }

  return {h, s, l};
}


function hslToRgb({h, s, l}) {
  const c = (1 - Math.abs(2 * l - 1)) * s,
        x = c * (1 - Math.abs(((h / 60) % 2) - 1)),
        m = l - c / 2;

  let rgb;
  if (h < 60)
    rgb = [c, x, 0];
  else if (h < 120)
    rgb = [x, c, 0];
  else if (h < 180)
    rgb = [0, c, x];
  else if (h < 240)
    rgb = [0, x, c];
  else if (h < 300)
    rgb = [x, 0, c];
  else
    rgb = [c, 0, x];

  return {
    r: Math.round((rgb[0] + m) * 255),
    g: Math.round((rgb[1] + m) * 255),
    b: Math.round((rgb[2] + m) * 255),
  };
}


class EdwColor {

  constructor(value) {
    this._rgb = parse(value);
  }

  rgb() {
    const {r, g, b} = this._rgb;
    return {
      array: () => [r, g, b],
      string: () => `rgb(${r}, ${g}, ${b})`,
    };
  }

  alpha() {
    return this._rgb.a;
  }

  darken(ratio = 0) {
    const hsl = rgbToHsl(this._rgb);
    const l = clamp(hsl.l - hsl.l * ratio, 0, 1);
    const {r, g, b} = hslToRgb({h: hsl.h, s: hsl.s, l});
    return `rgb(${r}, ${g}, ${b})`;
  }

  toString() {
    const {r, g, b, a} = this._rgb;
    return a === 1 ? `rgb(${r}, ${g}, ${b})` : `rgba(${r}, ${g}, ${b}, ${a})`;
  }
}


export default function Color(value) {
  return new EdwColor(value);
}
