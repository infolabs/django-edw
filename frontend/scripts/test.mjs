#!/usr/bin/env node
/*
 * Офлайн-прогон smoke-тестов фронтенда django-edw.
 *
 * Тесты собираются esbuild в один CJS-бандл (React 18.3 + react-dom/server из
 * предсобранного node_modules) и запускаются node: ни npm install, ни сеть,
 * ни headless-браузер не нужны.
 *
 * Usage: node scripts/test.mjs
 */
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import {
  FRONTEND_DIR,
  NODE_MODULES,
  baseOptions,
  esbuild,
} from './buildlib.mjs';

const {build} = esbuild;


// Тесты рендерят дерево компонентов без DOM (react-dom/server), но часть
// модулей EDW (actions/EntitiesActions) на этапе импорта обращается к window и к
// глобальному gettext из django-шаблонов. Даём минимальные заглушки — они не
// имитируют DOM, а только позволяют модулям загрузиться.
const BANNER = `
globalThis.gettext = globalThis.gettext || function (text) { return text; };
if (typeof globalThis.window === 'undefined') {
  globalThis.window = globalThis;
  globalThis.window.location = globalThis.window.location || {
    hash: '', search: '', pathname: '/',
  };
  globalThis.window.addEventListener = function () {};
  globalThis.window.removeEventListener = function () {};
  globalThis.window.scrollTo = function () {};
}
`;


async function main() {
  const workdir = fs.mkdtempSync(path.join(os.tmpdir(), 'edw-frontend-tests.'));
  const outfile = path.join(workdir, 'tests.cjs');

  try {
    await build({
      ...baseOptions(),
      entryPoints: [path.join(FRONTEND_DIR, 'tests', 'run.js')],
      outfile,
      format: 'cjs',
      platform: 'node',
      target: ['node18'],
      minify: false,
      sourcemap: false,
      legalComments: 'none',
      banner: {js: BANNER},
    });

    console.log(`  node_modules: ${NODE_MODULES}`);

    const result = spawnSync(process.execPath, [outfile], {
      encoding: 'utf8',
      env: Object.assign({}, process.env, {NODE_ENV: 'production'}),
    });

    if (result.stdout)
      process.stdout.write(result.stdout);
    if (result.stderr)
      process.stderr.write(result.stderr);
    if (result.error)
      throw result.error;
    if (result.status !== 0)
      process.exitCode = result.status === null ? 1 : result.status;
  } finally {
    fs.rmSync(workdir, {recursive: true, force: true});
  }
}


main().catch((error) => {
  if (error && error.stdout)
    process.stdout.write(error.stdout);
  if (error && error.stderr)
    process.stderr.write(error.stderr);
  console.error('TESTS FAIL');
  console.error(error && error.message ? error.message : error);
  process.exit(1);
});
