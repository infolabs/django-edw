import React, { Component } from 'react';
import ReactDOM from 'react-dom';
import cookie from 'react-cookies'


export default class BtnGroup extends Component {

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
    const { actions, entry_point_id, subj_ids, name, request_var, request_options } = this.props;
    let option = {};
    option[request_var] = value;
    let options = Object.assign(request_options, option);
    actions.selectDropdown(name, value);
    actions.notifyLoadingEntities();
    actions.getEntities(entry_point_id, subj_ids, this.fixOffset(options));
  }

  // componentDidMount() {
  //   document.body.addEventListener('click', this.handleBodyClick);
  // }
  //
  // componentWillUnmount() {
  //   document.body.removeEventListener('click', this.handleBodyClick);
  // }

  // handleBodyClick = (e) => {
  //   const area = ReactDOM.findDOMNode(this),
  //         { actions, name, open } = this.props;
  //   if (!area.contains(e.target) && open) {
  //     e.preventDefault();
  //     e.stopPropagation();
  //     this.props.actions.toggleDropdown(name);
  //   }
  // }

  handleOptionClick(e, value) {
    e.preventDefault();
    e.stopPropagation();
    const { entry_point_id, request_var  } = this.props;
    this.selectItem(value);
    const cookie_key = "datamart_prefs_" + entry_point_id + "_" + request_var;
    let expires = new Date();   
    expires.setTime(expires.getTime() + 2592000000); // 2592000000 = 30 * 24 * 60 * 60 * 1000
    cookie.save(cookie_key, encodeURI(value), { path: '/', expires: expires });
  }

  // handleSelectedClick(e) {
  //   e.preventDefault();
  //   e.stopPropagation();
  //   const { actions, name, open } = this.props;
  //   this.props.actions.toggleDropdown(name);
  // }

  render() {
    const { selected, options } = this.props;

    // let opts = {};
    // for (const opt of Object.keys(options)) {
    //   if (options[opt] != selected)
    //     opts[opt] = options[opt];
    // }

    // let ret = (
    //   <div className="ex-sort-dropdown">
    //     <a href="#"
    //        className="ex-btn ex-btn-default"
    //        onClick={(e) => { ::this.handleSelectedClick(e) } }>
    //       {selected}<span className="ex-icon-caret-down"></span>
    //     </a>
    //     <ul className={open ? "ex-dropdown-menu2": "ex-dropdown-menu2 ex-dropdown-hide"}>
    //       {Object.keys(opts).map(
    //         (k, i) => <li key={i} onClick={(e) => { ::this.handleOptionClick(e, k) } }>
    //           <a href="#" key={i}>{options[k]}</a>
    //         </li>
    //       )}
    //     </ul>
    //   </div>
    // );

      //disabled={ is_selected ? "disabled" : null }

    let ret = (
      <div className="ex-btn-group" role="group">
        {Object.keys(options).map(
          (k, i) => {
            const is_selected = options[k] == selected;
            return <button key={i} onClick={(e) => { ::this.handleOptionClick(e, k) } }
                            type="button"
                            className={"ex-btn ex-btn-default " + k + (is_selected ? ' active' : '')}
                   ><i className="ex-icon-slug"></i><span>{options[k]}</span></button>
          }
        )}


      </div>
    );

    return ret;
  }
}
