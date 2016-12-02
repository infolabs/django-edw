import React, { Component } from 'react';
import Dropdown from './Dropdown';

export default class HowMany extends Component {
  render() {
    const { dropdowns, actions, meta } = this.props,
          { limits, ordering, view_components } = dropdowns;

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


    let ret_components = "";
    if (ordering && Object.keys(view_components.options).length > 1) {
      ret_components = (
        <div className="col-sm-6 ex-order-by ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>Компоненты &nbsp; </span>
            </li>
            <li>
              <Dropdown name='view_components'
                        request_var={view_components.request_var}
                        request_options={meta.request_options}
                        open={view_components.open}
                        actions={actions}
                        selected={view_components.selected}
                        options={view_components.options}/>
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
                        count={meta.count}
                        options={limits.options}/>

            </li>
          </ul>
        </div>
      )
    }

    let statistics = "";
    if (meta.count) {
      const total = meta.count,
            offset = meta.offset,
            limit = meta.limit;

      let to = offset + limit;
      to = total < to ? total : to;

      statistics = (
        <div className="col-sm-3 ex-statistic">
          Элемент(ы) {offset + 1} - {to} из {total}
        </div>
      );
    }

    return (
      <div className="row">
        {ret_ordering}
        {ret_components}
        {ret_limits}
        {statistics}
      </div>
    );
  }
}
