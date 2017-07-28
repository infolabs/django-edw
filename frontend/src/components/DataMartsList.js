import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import {
  set_data_mart_list,
  change_active_data_mart
} from '../actions/DataMartListActions'
import Actions from '../actions/index'


class DataMartsList extends Component {

  constructor(props) {
      super(props);
      this.state = {
        data_entry_point: props.dom_attrs.getNamedItem('data-entry-point'),
        mart_id: props.mart_id
      }
  }

  componentWillMount() {

    const { data_entry_point, mart_id } = this.state,
      { set_data_mart_list } = this.props;

    let list = JSON.parse(data_entry_point.value);

    set_data_mart_list(list, parseInt(mart_id))

  }

  changeDataMart(datamart){

    const { change_active_data_mart } = this.props;

    change_active_data_mart(datamart.data_mart_pk);

    this.props.actions.notifyLoading();
    this.props.actions.loadTree(datamart.data_mart_pk, datamart.terms_ids);

    let request_options = {};

    request_options['terms'] = datamart.terms_ids;
    request_options['offset'] = 0;
    this.props.actions.notifyLoadingEntities();
    this.props.actions.getEntities(datamart.data_mart_pk, datamart.subj_ids, request_options);

  }

  render() {

    const { data_marts, active } = this.props;

    let is_active = (pk) => {
      if (pk == active) {
        return true
      } else {
        return false
      }
    };

    return data_marts && data_marts.length > 1 ? <div>
      <ul className="datamart-list">
        {data_marts.map((item, i) => {

          let pk = item.data_mart_pk;

          return <li
            key={`datamart-list_${i}`}
            className={is_active(pk) ? 'active' : ''}
            onClick={() => is_active(pk) ? null : this.changeDataMart(item)}
          >
            <span>{item.data_mart_name}</span>
          </li>

        })}
      </ul>
    </div> : null

  }

}

const mapState = (state) => ({
  data_marts: state.datamart_list.data_marts,
  active: state.datamart_list.active_mart
});


const mapDispatch = (dispatch) => ({
  dispatch: dispatch,
  set_data_mart_list: (data_marts, mart_id) => dispatch(set_data_mart_list(data_marts, mart_id)),
  actions: bindActionCreators(Actions, dispatch),
  change_active_data_mart: active => dispatch(change_active_data_mart(active))
});


export default connect(mapState, mapDispatch)(DataMartsList);