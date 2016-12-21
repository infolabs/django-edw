import React, { Component } from 'react';
import Paginator from 'components/Paginator';
import Entities from 'components/Entities';

export default class Related extends Component {
  render() {
    const { components, dom_attrs, mart_id } = this.props,
          data_mart_url_attr = dom_attrs.getNamedItem('data-data-mart-url'),
          data_mart_name_attr = dom_attrs.getNamedItem('data-data-mart-name');
    let mart_url = "",
        mart_name = "";
    if (data_mart_url_attr)
      mart_url = data_mart_url_attr.value;
    if (data_mart_name_attr)
      mart_name = data_mart_name_attr.value;

    return (
      <div>
        <div className="top-navigation">
          <div className="title-block">
            <h3><a href={mart_url} title={mart_name}>{mart_name}</a></h3>
          </div>
          <div className="pager-block">
            <Paginator dom_attrs={dom_attrs}
                       mart_id={mart_id}
                       hide_page_numbers={true}/>
          </div>
        </div>
        <div>
          <Entities dom_attrs={dom_attrs} mart_id={mart_id} />
        </div>
      </div>
    );
  }
}
