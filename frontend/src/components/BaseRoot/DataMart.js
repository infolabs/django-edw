import React, { Component } from 'react';

import Entities from 'components/Entities';
import TermsTree from 'components/TermsTree';
import Paginator from 'components/Paginator';
import ViewComponents from 'components/ViewComponents';
import Ordering from 'components/Ordering';
import Limits from 'components/Limits';
import Statistics from 'components/Statistics';
import Aggregation from 'components/Aggregation';


export default class DataMart extends Component {
  render() {
    const { dom_attrs, mart_id } = this.props;

    return (
      <div className="row">
        <div className="col-sm-4 col-md-3 sidebar-filter">
          <TermsTree dom_attrs={dom_attrs} mart_id={mart_id} />
        </div>
        <div className="col-sm-8 col-md-9">
          <div className="row">
            <div className="col-sm-6 col-md-3 ex-view-as ex-dropdown ex-state-closed">
              <ViewComponents dom_attrs={dom_attrs} mart_id={mart_id} />
            </div>
            <div className="col-sm-6 col-md-4 ex-order-by ex-dropdown ex-state-closed">
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
          <Paginator dom_attrs={dom_attrs} mart_id={mart_id} />
          <Aggregation dom_attrs={dom_attrs} mart_id={mart_id} />
        </div>
      </div>
    );
  }
}
