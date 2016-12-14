import React, { Component } from 'react';

export default class Rubricator extends Component {
  render() {
    const { components,  dom_attrs, mart_id } = this.props,
          { TermsTree, Entities, Paginator,
            ViewComponents, Ordering, Limits, Statistics } = components;

    return (
      <div className="row">
        <div className="col-sm-4 col-md-3 sidebar-filter">
          <TermsTree dom_attrs={dom_attrs} mart_id={mart_id} />
        </div>
        <div className="col-sm-8 col-md-9">
          <div className="row">
            <div className="col-sm-6 col-md-3 ex-order-by ex-dropdown ex-state-closed">
              <ViewComponents dom_attrs={dom_attrs} mart_id={mart_id} />
            </div>
            <div className="col-sm-6 col-md-3 ex-order-by ex-dropdown ex-state-closed">
              <Ordering dom_attrs={dom_attrs} mart_id={mart_id} />
            </div>
            <div className="col-sm-6 col-md-3 ex-howmany-items ex-dropdown ex-state-closed">
              <Limits dom_attrs={dom_attrs} mart_id={mart_id} />
            </div>
            <div className="col-sm-6 col-md-2 ex-statistic float-right">
              <Statistics dom_attrs={dom_attrs} mart_id={mart_id} />
            </div>
          </div>
          <Entities dom_attrs={dom_attrs} mart_id={mart_id} />
          <div className="row">
            <Paginator dom_attrs={dom_attrs} mart_id={mart_id} />
          </div>
        </div>
      </div>
    );
  }
}
