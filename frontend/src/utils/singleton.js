const _key = '_global_singleton_instance';

import {
  PLATFORM,
  NATIVE,
} from '../constants/Common';


export default class Singleton {

  static getWebInstance() {
    let instance = window[_key];
    if (!instance)
      instance = window[_key] = new Singleton();
    return instance;
  }

  static myInstance = null;

  static getNativeInstance() {
    if (Singleton.myInstance == null)
      Singleton.myInstance = new Singleton();

    return this.myInstance;
  }

  static getInstance() {
    return PLATFORM === NATIVE ? this.getNativeInstance() : this.getWebInstance();
  }
}
