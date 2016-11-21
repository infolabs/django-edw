import React, { Component } from 'react';

export default class Dropdown extends Component {
  render() {
    const { selected, options } = this.props;

    return (
      <div className="ex-sort-dropdown">
        <a href="#" className="ex-btn ex-btn-default ex-js-dropdown-toggle">
          {selected}<span className="ex-icon-caret-down"></span>
        </a>
        <ul className="ex-dropdown-menu2">
          {options.map(
            (option, i) => <li key={i}><a href="#">{option}</a></li>
          )}
        </ul>
      </div>
    );
  }
}
