import {
    PLATFORM,
    NATIVE,
} from '../constants/Common';

import Singleton from './singleton';


function getDomain() {
  return PLATFORM === NATIVE ? Singleton.getInstance().Domain : '';
}


function getUrls() {
  return PLATFORM === NATIVE ? Singleton.getInstance().Urls : Urls;
}


export default function getUrl(key, args = []) {
  return getDomain() + getUrls()[key](...args);
}
