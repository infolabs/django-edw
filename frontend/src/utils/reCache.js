import {
  RECACHE_RATE,
  PLATFORM,
  NATIVE,
} from '../constants/Common';


const rate = PLATFORM === NATIVE ? 1 : RECACHE_RATE;

export default function reCache(url) {
  const reCache = Math.round(new Date().getTime() / rate);
  return url.includes('?') ? `${url}&_=${reCache}` : `${url}?_=${reCache}`;
}
