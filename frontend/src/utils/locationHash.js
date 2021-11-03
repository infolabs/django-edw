const DM_PREFIX = '~dm';
const TERMS_PREFIX = 't=';
const OFFSET_PREFIX = 'o=';
const ALIKE_PREFIX = 'a=';

const TERMS_REGEX_POSTFIX  = TERMS_PREFIX + '(([0-9]+,?)+)';
const OFFSET_REGEX_POSTFIX  = OFFSET_PREFIX + '([0-9]+)';
const ALIKE_REGEX_POSTFIX  = ALIKE_PREFIX + '([0-9]+)';

const TERMS_REGEX  = new RegExp(DM_PREFIX + '([0-9]+)' + TERMS_REGEX_POSTFIX, 'g');
const OFFSET_REGEX  = new RegExp(DM_PREFIX + '([0-9]+)' + OFFSET_REGEX_POSTFIX, 'g');
const ALIKE_REGEX  = new RegExp(DM_PREFIX + '([0-9]+)' + ALIKE_REGEX_POSTFIX, 'g');


function replaceHash(newhash) {
  if ((`${newhash}`).charAt(0) !== '#')
    newhash = `#${newhash}`;
  history.replaceState(undefined, undefined, newhash);
}


function setHash(hash, head, postfix, data) {
  let newHash = head + data;
  hash = hash.replace(new RegExp(head + postfix, 'g'), '');
  return hash + newHash;
}


export function setOffset(dataMartId, offset) {
  let hash = window.location.hash;
  const hashHead = `${DM_PREFIX}${dataMartId}`;
  hash = setHash(hash, hashHead, OFFSET_REGEX_POSTFIX, OFFSET_PREFIX + (offset || 0));

  replaceHash(hash);
}


export function setDatamartHash(dataMartId, terms_ids, offset = 0) {
  let hash = window.location.hash;

  const hashHead = `${DM_PREFIX}${dataMartId}`;
  hash = setHash(hash, hashHead, TERMS_REGEX_POSTFIX, TERMS_PREFIX + terms_ids.join(','));
  hash = setHash(hash, hashHead, OFFSET_REGEX_POSTFIX, OFFSET_PREFIX + (offset || 0));

  replaceHash(hash);
}

export function setAlike(dataMartId, alikeId) {
  let hash = window.location.hash;
  const hashHead = `${DM_PREFIX}${dataMartId}`;

  if (!alikeId) {
    const regEx = new RegExp(`(${hashHead}${ALIKE_PREFIX})((\\d*))`),
          res = hash.match(regEx)[0];

    hash = hash.replace(res, '');
  } else {
    hash = setHash(hash, hashHead, ALIKE_REGEX_POSTFIX, `${ALIKE_PREFIX}${alikeId}`);
  }
  replaceHash(hash);
}


function setData(dataMarts, regex, key, func) {
  let matches = regex.exec(window.location.hash);
  if (matches) {
    const mart = dataMarts[matches[1]] || {};
    mart[key] = func(matches);
    dataMarts[matches[1]] = mart;
  }
}


export function getDatamartsData() {
  const dataMarts = {};
  setData(dataMarts, ALIKE_REGEX, 'alike', m => parseInt(m[2], 10));
  setData(dataMarts, OFFSET_REGEX, 'offset', m => parseInt(m[2], 10));
  setData(dataMarts, TERMS_REGEX, 'terms', m => m[2].split(',').map(x => parseInt(x, 10)));

  return dataMarts;
}
