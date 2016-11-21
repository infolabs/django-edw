import React, { Component } from 'react';
import ReactDOM from 'react-dom';

export default class Dropdown extends Component {

  componentDidMount() {
    document.body.addEventListener('click', this.handleBodyClick);
  }

  componentWillUnmount() {
    document.body.removeEventListener('click', this.handleBodyClick);
  }

  handleBodyClick = (evt) => {
    const { actions, name, open } = this.props;
    if (open) {
      this.props.actions.toggleDropdown(name);
    }
  }

  handleOptionClick(e, value) {
    e.preventDefault();
    e.stopPropagation();
    const { actions, name, request_var, request_options } = this.props;
    let option = {};
    option[request_var] = value;
    let options = Object.assign(request_options, option);
    this.props.actions.selectDropdown(name, value);
    this.props.actions.notifyLoading();
    this.props.actions.getEntities(options);
  }

  handleSelectedClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { actions, name } = this.props;
    this.props.actions.toggleDropdown(name);
  }

  render() {
    const { selected, options, open } = this.props;

    return (
      <div className="ex-sort-dropdown">
        <a href="#"
           className="ex-btn ex-btn-default"
           onClick={(e) => { ::this.handleSelectedClick(e) } }>
          {selected}<span className="ex-icon-caret-down"></span>
        </a>
        <ul className={open ? "ex-dropdown-menu2": "ex-dropdown-menu2 ex-dropdown-hide"}>
          {Object.keys(options).map(
            (k, i) => <li key={i} onClick={(e) => { ::this.handleOptionClick(e, k) } }>
              <a href="#" key={i}>{options[k]}</a>
            </li>
          )}
        </ul>
      </div>
    );
  }
}
