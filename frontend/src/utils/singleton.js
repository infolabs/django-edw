const _key = '_global_singleton_instance';


export default class Singleton{
  // web
  constructor() {
    let instance = window[_key];
    if ( !instance ){
      instance = window[_key] = this;
    }
    return instance;
  }

  // mobile
  static myInstance = null;

  static getInstance() {
    if (Singleton.myInstance == null)
      Singleton.myInstance = new Singleton();

    return this.myInstance;
  }
}
