export default class Singleton {

  static myInstance = null;

  /*
   * @returns {Singleton}
   */
  static getInstance() {
    if (Singleton.myInstance == null)
      Singleton.myInstance = new Singleton();

    return this.myInstance;
  }
}
