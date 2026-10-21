/*
 * Раннер офлайн smoke-тестов фронтенда.
 *
 * Собирается scripts/test.mjs в CJS-бандл и запускается node; сети, DOM и
 * npm install не требует. Итоговая строка с числами парсится в scripts/check.sh.
 */
import dataMartTest from './datamart.test.js';
import filtersTest from './filters.test.js';
import termsTreeTest from './terms-tree.test.js';


const SUITES = [
  ['terms-tree', termsTreeTest],
  ['filters', filtersTest],
  ['datamart', dataMartTest],
];


export function main() {
  const failures = [];
  let passed = 0;

  console.log('== frontend smoke tests (react-dom/server) ==');

  for (const [name, suite] of SUITES) {
    try {
      suite();
      passed++;
      console.log(`  PASS ${name}`);
    } catch (error) {
      failures.push(`${name}: ${error && error.message ? error.message : error}`);
      console.log(`  FAIL ${name}: ${error && error.message ? error.message : error}`);
      if (error && error.stack)
        console.log(error.stack.split('\n').slice(1, 4).join('\n'));
    }
  }

  console.log(`TESTS passed=${passed} failed=${failures.length}`);

  if (failures.length)
    process.exitCode = 1;
}


main();
