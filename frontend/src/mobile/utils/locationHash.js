const DM_PREFIX = '~dm';
const TERMS_PREFIX = 't=';
const OFFSET_PREFIX = 'o=';

const TERMS_REGEX_POSTFIX  = TERMS_PREFIX + '(([0-9]+,?)+)';
const OFFSET_REGEX_POSTFIX  = OFFSET_PREFIX + '([0-9]+)';

const TERMS_REGEX  = new RegExp(DM_PREFIX + '([0-9]+)' + TERMS_REGEX_POSTFIX, 'g');
const OFFSET_REGEX  = new RegExp(DM_PREFIX + '([0-9]+)' + OFFSET_REGEX_POSTFIX, 'g');


function replaceHash(newhash) {
  if ((''+newhash).charAt(0) !== '#')
    newhash = '#' + newhash;
  history.replaceState(undefined, undefined, newhash);
}


function setHash(hash, head, postfix, data) {
  let newHash = head + data;
  hash = hash.replace(new RegExp(head + postfix, 'g'), '');
  return hash + newHash;
}


export function setOffset(datamart_id, offset) {
  let hash = window.location.hash;
  const hashHead = DM_PREFIX + datamart_id;
  hash = setHash(hash, hashHead, OFFSET_REGEX_POSTFIX, OFFSET_PREFIX + (offset || 0));

  replaceHash(hash);
}


export function setDatamartHash(datamart_id, terms_ids, offset=0) {
  let hash = window.location.hash;

  const hashHead = DM_PREFIX + datamart_id;
  hash = setHash(hash, hashHead, TERMS_REGEX_POSTFIX, TERMS_PREFIX + terms_ids.join(','));
  hash = setHash(hash, hashHead, OFFSET_REGEX_POSTFIX, OFFSET_PREFIX + (offset || 0));

  replaceHash(hash);
}


function setData(datamarts, regex, key, func) {
  let matches;
  while ((matches = regex.exec(window.location.hash))) {
    const mart = datamarts[matches[1]] || {};
    mart[key] = func(matches);
    datamarts[matches[1]] = mart;
  }
}


export function getDatamartsData() {
  const datamarts = {};
  setData(datamarts, OFFSET_REGEX, 'offset', m => parseInt(m[2]));
  setData(datamarts, TERMS_REGEX, 'terms', m => m[2].split(",").map(x => parseInt(x)));

  return datamarts;
}
