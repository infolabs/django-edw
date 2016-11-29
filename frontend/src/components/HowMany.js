import React, { Component } from 'react';
import Dropdown from './Dropdown';

export default class HowMany extends Component {
  render() {
    const { dropdowns, actions, meta } = this.props,
          { limits, ordering } = dropdowns;

    let ret_ordering = "";
    if (ordering && Object.keys(ordering.options).length > 1) {
      ret_ordering = (
        <div className="col-sm-6 ex-order-by ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>Сортировать по &nbsp; </span>
            </li>
            <li>
              <Dropdown name='ordering'
                        request_var={ordering.request_var}
                        request_options={meta.request_options}
                        open={ordering.open}
                        actions={actions}
                        selected={ordering.selected}
                        options={ordering.options}/>
            </li>
          </ul>
        </div>
      )
    }

    let ret_limits = "";
    if (limits && Object.keys(limits.options).length > 1) {
      ret_limits = (
        <div className="col-sm-3 ex-howmany-items ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>Количество &nbsp; </span>
            </li>
            <li>
              <Dropdown name='limits'
                        request_var={limits.request_var}
                        request_options={meta.request_options}
                        open={limits.open}
                        actions={actions}
                        selected={limits.selected}
                        options={limits.options}/>

            </li>
          </ul>
        </div>
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
        {ret_ordering}
        {ret_limits}
        {statistics}
      </div>
    );
  }
}
