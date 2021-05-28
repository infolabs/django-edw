export default class Singleton {
  static instance = null;
  /*
   * @returns {Singleton}
   */
  static getInstance() {
    if (Singleton.instance == null)
      Singleton.instance = new Singleton();

    return this.instance;
  }
}
