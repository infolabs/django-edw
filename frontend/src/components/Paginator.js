import React, { Component } from 'react';

export default class Paginator extends Component {

  render() {
    return (
      <div className="ex-catalog-pagination">
        <ul className="ex-pagination">
          <li className="ex-disabled ex-prev">
            <a href="#"><i className="ex-icon-chevron-left"></i></a>
          </li>
          <li className="ex-active"><span>1</span></li>
          <li><a href="#" className="js-page" data-page="2">2</a></li>
          <li><a href="#" className="js-page" data-page="3">3</a></li>
          <li><a href="#" className="js-page" data-page="4">4</a></li>
          <li><span className="ex-separator">…</span></li>
          <li><a href="#" className="js-page" data-page="273">273</a></li>
          <li><a href="#" className="js-page" data-page="274">274</a></li>
          <li className="ex-next">
            <a href="#"><i className="ex-icon-chevron-right"></i></a>
          </li>
        </ul>
      </div>
    );
  }
}

