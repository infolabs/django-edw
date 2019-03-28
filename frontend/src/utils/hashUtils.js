export function hashCode(s) {
  let hash = 0, i, chr;
  if (s.length === 0) return hash;
  for (i = 0; i < s.length; i++) {
    chr   = s.charCodeAt(i);
    hash  = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash);
}


export default function cookieKey(data_mart_id, path, setting) {
  return `dm_${data_mart_id}_${hashCode(path)}_${setting}`;
}
