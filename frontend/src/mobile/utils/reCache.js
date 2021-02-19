import {
    RECACHE_RATE
} from '../constants/TermsTree'


export default function reCache(url) {
    const recache = Math.round(new Date().getTime() / RECACHE_RATE);
    return url+'?_='+recache
}
