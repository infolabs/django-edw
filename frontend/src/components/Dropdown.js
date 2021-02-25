import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import cookie from 'react-cookies';
import cookieKey from "../utils/hashUtils";
import parseRequestParams from 'utils/parseRequestParams';


export default class Dropdown extends Component {

  fixOffset(options = {}) {
    const total = this.props.count,
          offset = options.offset,
          limit = options.limit;
    if (total && offset && limit && total < offset + limit) {
        options.offset = total - limit - total % limit;
    }
    return options;
  }

  selectItem(value) {
    const { actions, entry_point_id, subj_ids, name, request_var, request_options, entry_points } = this.props;

    let option = {};
    option[request_var] = value;
    let options = Object.assign(request_options, option);
    actions.selectDropdown(name, value);
    actions.notifyLoadingEntities();
    if (entry_points){
      const request_params = entry_points[entry_point_id].request_params,
            parms = parseRequestParams(request_params),
            options_arr = parms.options_arr;
      actions.getEntities(entry_point_id, subj_ids, this.fixOffset(options), options_arr);
    } else {
      actions.getEntities(entry_point_id, subj_ids, this.fixOffset(options));
    }
  }

  componentDidMount() {
    document.body.addEventListener('click', this.handleBodyClick);
  }

  componentWillUnmount() {
    document.body.removeEventListener('click', this.handleBodyClick);
  }

  handleBodyClick = (e) => {
    const area = ReactDOM.findDOMNode(this),
          { actions, name, open } = this.props;
    if (!area.contains(e.target) && open) {
      e.preventDefault();
      e.stopPropagation();
      actions.toggleDropdown(name);
    }
  };

  handleOptionClick(e, value) {
    e.preventDefault();
    e.stopPropagation();
    const { entry_point_id, request_var  } = this.props;
    this.selectItem(value);
    const cookie_key = cookieKey(entry_point_id, document.location.pathname, request_var);
    let expires = new Date();
    expires.setTime(expires.getTime() + 2592000000); // 2592000000 = 30 * 24 * 60 * 60 * 1000
    cookie.save(cookie_key, encodeURI(value), { path: '/', expires: expires });
  }

  handleSelectedClick(e) {
    e.preventDefault();
    e.stopPropagation();
    const { actions, name } = this.props;
    actions.toggleDropdown(name);
  }

  render() {
    const { selected, options, open } = this.props;

    let opts = {};
    for (const opt of Object.keys(options)) {
      if (options[opt] != selected)
        opts[opt] = options[opt];
    }

    return (
        <div className="ex-sort-dropdown">
          <a href="#"
             className="ex-btn ex-btn-default"
             onClick={(e) => { ::this.handleSelectedClick(e); } }>
            {selected}<span className="ex-icon-caret-down"></span>
          </a>
          <ul className={open ? "ex-dropdown-menu2": "ex-dropdown-menu2 ex-dropdown-hide"}>
            {Object.keys(opts).map(
              (k, i) => <li key={i} onClick={(e) => { ::this.handleOptionClick(e, k); } }>
                <a href="#" key={i}>{options[k]}</a>
              </li>
            )}
          </ul>
        </div>
      );
  }
}
