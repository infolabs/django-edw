import React, {Component} from 'react';
import cookie from 'react-cookies';
import cookieKey from '../utils/hashUtils';
import parseRequestParams from 'utils/parseRequestParams';

export default class BtnGroup extends Component {

  fixOffset(options = {}) {
    const total = this.props.count,
      offset = options.offset,
      limit = options.limit;
    if (total && offset && limit && total < offset + limit)
      options.offset = total - limit - total % limit;

    return options;
  }

  selectItem(value) {
    const {actions, entry_point_id, entry_points, subj_ids, name, request_var, request_options} = this.props;
    let option = {};
    option[request_var] = value;
    let options = Object.assign(request_options, option);
    actions.selectDropdown(name, value);
    actions.notifyLoadingEntities();
    const params = {
      mart_id: entry_point_id,
      options_obj: this.fixOffset(options),
      subj_ids,
    };
    if (entry_points) {
      let request_params = entry_points[entry_point_id].request_params || [];
      request_params = parseRequestParams(request_params);
      const {options_arr} = request_params;
      params.options_arr = options_arr;
    }
    actions.getEntities(params);
  }

  handleOptionClick(e, value) {
    e.preventDefault();
    e.stopPropagation();
    const {entry_point_id, request_var} = this.props;
    this.selectItem(value);
    const cookie_key = cookieKey(entry_point_id, document.location.pathname, request_var);
    let expires = new Date();
    expires.setTime(expires.getTime() + 2592000000); // 2592000000 = 30 * 24 * 60 * 60 * 1000
    cookie.save(cookie_key, encodeURI(value), {path: '/', expires: expires});
  }

  render() {
    const {selected, options} = this.props;

    let ret = (
      <div className="ex-btn-group" role="group">
        {Object.keys(options).map(
          (k, i) => {
            const is_selected = options[k] === selected;
            return <a
              key={i}
              onClick={(e) => {
                is_selected ? null : ::this.handleOptionClick(e, k);
              }}
              className={'ex-btn ex-btn-default ' + k + (is_selected ? ' active' : '')}
            >
              <i className="ex-icon-slug"/><span>{options[k]}</span>
            </a>;
          }
        )}
      </div>
    );

    return ret;
  }
}
