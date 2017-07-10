import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../../actions/index'
import Paginator from 'components/Paginator';
import Entities from 'components/Entities';

class Related extends Component {
  render() {
    const { entities, dom_attrs, mart_id } = this.props,
          data_mart_url_attr = dom_attrs.getNamedItem('data-data-mart-url'),
          data_mart_name_attr = dom_attrs.getNamedItem('data-data-mart-name');

    const count = entities.meta.count;

    let mart_url = "",
        mart_name = "";
    if (data_mart_url_attr)
      mart_url = data_mart_url_attr.value;
    if (data_mart_name_attr)
      mart_name = data_mart_name_attr.value;

    return (
      <div className="ex-related-datamart" data-data-count={count}>
        <div className="row">
          <div className="col-md-9 ex-title">
            { mart_url != '' ? (
            <h3><a href={mart_url} title={mart_name}>{mart_name}</a></h3>
            ) : (
            <h3>{mart_name}</h3>
            )}
          </div>
          <div className="col-md-3 ex-paginator">
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

function mapState(state) {
  return {
    entities: state.entities.items,
  };
}

function mapDispatch(dispatch) {
  return {
    actions: bindActionCreators(Actions, dispatch),
    dispatch: dispatch
  };
}


export default connect(mapState, mapDispatch)(Related);
