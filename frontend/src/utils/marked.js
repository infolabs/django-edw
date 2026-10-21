/*
 * Совместимый доступ к marked.
 *
 * В офлайн-дереве зависимостей стоит marked 12 (ESM, именованный экспорт
 * `marked`), а объявленная в package.json ^0.3.5 отдаёт CJS-функцию как
 * module.exports. Обёртка выбирает доступную форму, чтобы исходники работали
 * с обеими версиями без правок в местах вызова.
 */
import * as markedModule from 'marked';


const marked = markedModule.default || markedModule.marked || markedModule;

export default marked;
