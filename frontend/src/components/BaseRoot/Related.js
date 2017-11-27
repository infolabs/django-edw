import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import Actions from '../../actions/index'
import Paginator from 'components/Paginator';
import Entities from 'components/Entities';
import DataMartsList from 'components/DataMartsList'


class Related extends Component {

  render() {

    const { entities, dom_attrs, mart_id } = this.props,
          data_mart_url_attr = dom_attrs.getNamedItem('data-data-mart-url'),
          data_mart_name_attr = dom_attrs.getNamedItem('data-data-mart-name'),
          data_data_mart_limit = dom_attrs.getNamedItem('data-data-mart-limit'),
          data_data_mart_pk = dom_attrs.getNamedItem('data-data-mart-pk');

    const count = entities.meta.count;

    let limit = data_data_mart_limit && data_data_mart_limit.value ? data_data_mart_limit.value : null;

    let mart_url = "",
        mart_name = "";
    if (data_mart_url_attr)
      mart_url = data_mart_url_attr.value;
    if (data_mart_name_attr)
      mart_name = data_mart_name_attr.value;

    let el_with_count = ['ex-data-mart', 'ex-data-mart-container'];

    if (data_data_mart_pk) {
      for(let item of el_with_count){
        let elements = document.getElementsByClassName(item);
        for (let element of elements) {
          let pk = element.attributes.getNamedItem('data-data-mart-pk')
            ? element.attributes.getNamedItem('data-data-mart-pk').value : null;
          if (pk && pk == data_data_mart_pk.value) {
            element.setAttribute("data-data-count", count);
          }
        }
      }
    }

    return (
      <div className="ex-related-datamart">
        <div className="row">
          <div className="col-sm-12 col-md-12">
            {
              dom_attrs.getNamedItem('data-entry-point') ? <DataMartsList
                dom_attrs={dom_attrs}
                mart_id={mart_id}
              /> : null
            }
          </div>
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
          <Entities dom_attrs={dom_attrs} mart_id={mart_id} limit={limit} />
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
