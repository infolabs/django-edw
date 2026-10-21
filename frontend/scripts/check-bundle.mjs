#!/usr/bin/env node
/*
 * Проверка загружаемости production-бандла.
 *
 * Бандл исполняется в vm-песочнице с минимальными заглушками DOM (не эмуляция
 * браузера, а проверка того, что бандл не тянет node-глобалов вроде require/module
 * и что инициализация входа — вставка скомпилированных стилей и обход контейнеров
 * .ex-data-mart — проходит без исключений).
 *
 * Usage: node scripts/check-bundle.mjs [bundle.js]
 */
import fs from 'node:fs';
import vm from 'node:vm';
import {TextDecoder as NodeTextDecoder, TextEncoder as NodeTextEncoder} from 'node:util';

import {BUNDLE_FILE} from './buildlib.mjs';


function createElement(tagName) {
  const node = {
    nodeName: tagName.toUpperCase(),
    tagName: tagName.toUpperCase(),
    attributes: {},
    children: [],
    style: {},
    textContent: '',
    setAttribute(name, value) {
      this.attributes[name] = value;
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attributes, name)
        ? this.attributes[name]
        : null;
    },
    hasAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attributes, name);
    },
    removeAttribute(name) {
      delete this.attributes[name];
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    insertBefore(child) {
      this.children.push(child);
      return child;
    },
    removeChild(child) {
      return child;
    },
    addEventListener() {},
    removeEventListener() {},
    getBoundingClientRect() {
      return {top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0};
    },
  };
  return node;
}


function createSandbox(injected) {
  const head = createElement('head');
  const body = createElement('body');
  const documentElement = createElement('html');

  const document = {
    head,
    body,
    documentElement,
    createElement(tagName) {
      const node = createElement(tagName);
      injected.push(node);
      return node;
    },
    createTextNode(text) {
      return {nodeType: 3, textContent: text};
    },
    createDocumentFragment() {
      return createElement('fragment');
    },
    querySelector: () => null,
    querySelectorAll: () => [],
    getElementsByClassName: () => [],
    getElementsByTagName: () => [],
    addEventListener() {},
    removeEventListener() {},
  };

  const sandbox = {
    console,
    document,
    gettext: (text) => text,
    Promise,
    TextDecoder: NodeTextDecoder,
    TextEncoder: NodeTextEncoder,
    clearInterval,
    clearTimeout,
    fetch: () => Promise.reject(new Error('offline')),
    setInterval,
    setTimeout,
  };

  sandbox.window = sandbox;
  sandbox.self = sandbox;
  sandbox.navigator = {userAgent: 'edw-bundle-check'};
  sandbox.location = {hash: '', pathname: '/', search: ''};
  sandbox.addEventListener = () => {};
  sandbox.removeEventListener = () => {};

  return sandbox;
}


function main() {
  const bundle = process.argv[2] ? process.argv[2] : BUNDLE_FILE;
  const code = fs.readFileSync(bundle, 'utf8');
  const injected = [];

  vm.runInNewContext(code, createSandbox(injected), {filename: bundle});

  const styles = injected.filter(
    (node) => node && node.attributes && node.attributes['data-edw-style'] !== undefined
  );

  if (!styles.length)
    throw new Error('бандл не вставил скомпилированные less-стили');

  const css = styles.map((style) => style.children.map((child) => child.textContent).join('')).join('');
  if (!/\.ex-/.test(css))
    throw new Error('вставленный CSS не содержит классов EDW (.ex-*)');

  console.log(`  бандл исполняется: стилей вставлено ${styles.length}, CSS ${css.length} символов`);
}

try {
  main();
} catch (error) {
  console.error('BUNDLE LOAD FAIL');
  console.error(error && error.message ? error.message : error);
  process.exit(1);
}
