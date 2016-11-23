import React, { Component } from 'react';
import Dropdown from './Dropdown';

export default class HowMany extends Component {
  render() {
    const { dropdowns, actions, meta } = this.props,
          { limits, ordering } = dropdowns;

    let ret_ordering = "";
    if (ordering) {
      ret_ordering = (
        <Dropdown name='ordering'
                  request_var={ordering.request_var}
                  request_options={meta.request_options}
                  open={ordering.open}
                  actions={actions}
                  selected={ordering.selected}
                  options={ordering.options}/>
      )
    }
    let ret_limits = "";
    if (limits) {
      ret_limits = (
        <Dropdown name='limits'
                  request_var={limits.request_var}
                  request_options={meta.request_options}
                  open={limits.open}
                  actions={actions}
                  selected={limits.selected}
                  options={limits.options}/>
      )
    }

    let statistics = "";
    if (meta.count) {
      statistics = (
        <div className="col-sm-3 ex-statistic">
          Элемент(ы) {meta.offset + 1} - {meta.limit} из {meta.count}
        </div>
      );
    }

    return (
      <div className="row">
        <div className="col-sm-6 ex-order-by ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>Сортировать по &nbsp; </span>
            </li>
            <li>
              {ret_ordering}
            </li>
          </ul>
        </div>

        <div className="col-sm-3 ex-howmany-items ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>Количество &nbsp; </span>
            </li>
            <li>
              {ret_limits}
            </li>
          </ul>
        </div>
        {statistics}
      </div>
    );
  }
}
