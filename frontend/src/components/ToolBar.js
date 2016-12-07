import React, { Component } from 'react';
import Dropdown from './Dropdown';

export default class ToolBar extends Component {
  render() {
    const { dropdowns, actions, meta, mart_id } = this.props,
          { limits, ordering, view_components } = dropdowns;

    let ret_ordering = "";
    if (ordering && Object.keys(ordering.options).length > 1) {
      ret_ordering = (
        <div className="col-sm-6 col-md-4 ex-order-by ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>{gettext("Sort by")} &nbsp; </span>
            </li>
            <li>
              <Dropdown name='ordering'
                        mart_id={mart_id}
                        request_var={ordering.request_var}
                        request_options={meta.request_options}
                        subj_ids={meta.subj_ids}
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
        <div className="col-sm-6 col-md-3 ex-order-by ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>{gettext("View as")} &nbsp; </span>
            </li>
            <li>
              <Dropdown name='view_components'
                        request_var={view_components.request_var}
                        mart_id={mart_id}
                        subj_ids={meta.subj_ids}
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

    let ret_limits = "",
        limit_options = {};

    if (limits) {
      // cut limits lower than count
      let max_opt_value = 0,
          max_value = 0;
      for (const key of Object.keys(limits.options)) {
        const value = limits.options[key]
        max_opt_value = value > max_opt_value ? value : max_opt_value;
        if (key == meta.selected || value <= meta.count) {
          max_value = value > max_value ? value : max_value;
          limit_options[key] = value;
        }
      }
      if (max_value < meta.count && meta.count < max_opt_value)
        limit_options[meta.count] = meta.count;
    }

    if (limits && Object.keys(limit_options).length > 1) {
      ret_limits = (
        <div className="col-sm-3 col-md-2 ex-howmany-items ex-dropdown ex-state-closed">
          <ul className="ex-inline">
            <li>
              <span>{gettext("Quantity")} &nbsp; </span>
            </li>
            <li>
              <Dropdown name='limits'
                        mart_id={mart_id}
                        request_var={limits.request_var}
                        request_options={meta.request_options}
                        subj_ids={meta.subj_ids}
                        open={limits.open}
                        actions={actions}
                        selected={limits.selected}
                        count={meta.count}
                        options={limit_options}/>

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
        <div className="col-sm-3 col-md-3 ex-statistic">
          {gettext("Element(s)")} {offset + 1} - {to} {gettext("from")} {total}
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
