import {
    RECACHE_RATE,
    PLATFORM,
    NATIVE,
} from '../constants/Common';


const rate = PLATFORM === NATIVE ? 1 : RECACHE_RATE;

export default function reCache(url) {
  const recache = Math.round(new Date().getTime() / rate);
  if (url.includes('?'))
    return `${url}&_=${recache}`;
  else
    return `${url}?_=${recache}`;
}
