/*
 * Общие для офлайн-сборки (scripts/build.mjs) и офлайн-тестов (scripts/test.mjs)
 * помощники: разрешение предсобранного node_modules и плагины esbuild.
 *
 * Никаких npm install: пакеты берутся из EDW_NODE_MODULES (по умолчанию —
 * /home/agent/workspace/venvs/edw-frontend/node_modules).
 */
import fs from 'node:fs';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';


export const FRONTEND_DIR = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const REPO_DIR = path.resolve(FRONTEND_DIR, '..');
export const SRC_DIR = path.join(FRONTEND_DIR, 'src');
export const VENDOR_DIR = path.join(SRC_DIR, 'vendor');

export const NODE_MODULES = process.env.EDW_NODE_MODULES
  || process.env.NODE_PATH
  || '/home/agent/workspace/venvs/edw-frontend/node_modules';

export const BUNDLE_DIR = path.join(REPO_DIR, 'backend', 'edw', 'static', 'edw', 'js');
export const BUNDLE_FILE = path.join(BUNDLE_DIR, 'bundle.js');

// ESM-резолвер node не использует NODE_PATH, поэтому инструменты сборки
// (esbuild, less) подгружаются из предсобранного дерева через createRequire.
const nodeModulesRequire = createRequire(path.join(NODE_MODULES, 'index.js'));

export const esbuild = nodeModulesRequire('esbuild');
export const less = nodeModulesRequire('less');

// Пакеты, объявленные в package.json, но отсутствующие в офлайн-дереве.
// Если пакет установлен — используется он сам, иначе — заглушка из src/vendor.
export const OPTIONAL_PACKAGES = {
  'react-google-maps': path.join(VENDOR_DIR, 'react-google-maps.js'),
  'react-yandex-maps': path.join(VENDOR_DIR, 'react-yandex-maps.js'),
  'color': path.join(VENDOR_DIR, 'color.js'),
};


export function isInstalled(name) {
  const candidates = [
    path.join(NODE_MODULES, name, 'package.json'),
    path.join(FRONTEND_DIR, 'node_modules', name, 'package.json'),
  ];
  return candidates.some((candidate) => fs.existsSync(candidate));
}


// Less компилируется в JS-модуль, который вставляет готовый CSS в документ —
// это сохраняет прежнее поведение webpack style-loader (стили приезжают
// вместе с бандлом, отдельный <link> в шаблонах не нужен).
function styleInjectionModule(css, filename) {
  return `(function () {
  if (typeof document === 'undefined')
    return;
  var css = ${JSON.stringify(css)};
  var attr = 'data-edw-style';
  var id = ${JSON.stringify(path.basename(filename))};
  var existing = document.querySelector('style[' + attr + '="' + id + '"]');
  if (existing)
    existing.textContent = css;
  else {
    var style = document.createElement('style');
    style.setAttribute(attr, id);
    style.appendChild(document.createTextNode(css));
    document.head.appendChild(style);
  }
})();
`;
}


export const lessPlugin = {
  name: 'edw-less',
  setup(build) {
    build.onLoad({filter: /\.less$/}, async (args) => {
      const source = await fs.promises.readFile(args.path, 'utf8');
      // math: 'always' — старая (less 2/3) семантика арифметики: исходники EDW
      // полагаются на вычисление выражений без скобок.
      const rendered = await less.render(source, {
        filename: args.path,
        paths: [path.dirname(args.path)],
        math: 'always',
        javascriptEnabled: false,
      });
      return {
        contents: styleInjectionModule(rendered.css, args.path),
        loader: 'js',
        resolveDir: path.dirname(args.path),
      };
    });
  },
};


export const optionalVendorPlugin = {
  name: 'edw-optional-vendor',
  setup(build) {
    build.onResolve({filter: /^(react-google-maps|react-yandex-maps|color)$/}, (args) => {
      const fallback = OPTIONAL_PACKAGES[args.path];
      if (!fallback)
        return null;
      if (isInstalled(args.path))
        return null;
      return {path: fallback};
    });
  },
};


// webpack-конфиг разрешал модули через resolve.modules (src первым каталогом),
// поэтому в исходниках встречаются импорты вида 'components/Root',
// 'constants/Entities', 'reducers'. Здесь то же самое: сначала src, потом
// настоящий node_modules предсобранного дерева.
export const srcAliasPlugin = {
  name: 'edw-src-alias',
  setup(build) {
    build.onResolve({filter: /^[^.@/]/}, (args) => {
      const base = path.join(SRC_DIR, args.path);
      const candidates = [base, `${base}.js`, path.join(base, 'index.js')];
      for (const candidate of candidates) {
        if (fs.existsSync(candidate) && fs.statSync(candidate).isFile())
          return {path: candidate};
      }
      return null;
    });
  },
};


export function baseOptions() {
  return {
    absWorkingDir: FRONTEND_DIR,
    bundle: true,
    nodePaths: [NODE_MODULES],
    // Исходники EDW — .js с JSX (как в webpack babel-loader).
    loader: {'.js': 'jsx'},
    jsx: 'transform',
    define: {
      'process.env.NODE_ENV': '"production"',
    },
    plugins: [optionalVendorPlugin, srcAliasPlugin, lessPlugin],
    logLevel: 'silent',
  };
}
