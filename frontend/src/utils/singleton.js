const _key = '_global_singleton_instance';


class Singleton{
    constructor() {
        let instance = window[_key];
        if ( !instance ){
              instance = window[_key] = this;
        }
        return instance;
      }
}


module.exports = Singleton;