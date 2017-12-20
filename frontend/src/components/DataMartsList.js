import { connect } from 'react-redux';
import { bindActionCreators } from 'redux';
import React, { Component } from 'react';
import parseRequestParams from 'utils/parseRequestParams';

export default class DataMartsList extends Component {

  constructor(props) {
      super(props);
      this.state = {
        entry_points: props.entry_points,
        entry_point_id: props.entry_point_id
      }
  }

  changeDataMart(pk) {

    const { entry_points, change_active_data_mart } = this.props,
            request_params = entry_points[pk].request_params || [];
    this.props.actions.changeActiveDataMart(pk);

    const parms = parseRequestParams(request_params),
          term_ids = parms.term_ids,
          subj_ids = parms.subj_ids,
          options_arr = parms.options_arr;

    this.props.actions.notifyLoading();
    this.props.actions.loadTree(pk, term_ids);

    let request_options = {};

    request_options['terms'] = term_ids;
    request_options['offset'] = 0;
    this.props.actions.notifyLoadingEntities();
    this.props.actions.getEntities(pk, subj_ids, request_options, options_arr);

  }

  render() {

    const { entry_points, entry_point_id } = this.props;

    let is_active = (pk) => pk == entry_point_id;


    return entry_points && Object.keys(entry_points).length > 1 ? <div>
      <ul className="datamart-list">
        {Object.keys(entry_points).map((key, i) => {

          const item = entry_points[key];

          return <li
            key={`datamart-list_${i}`}
            className={is_active(key) ? 'active' : ''}
            onClick={() => is_active(key) ? null : this.changeDataMart(key)}
          >
            <span>{item.name}</span>
          </li>

        })}
      </ul>
    </div> : null

  }

}

