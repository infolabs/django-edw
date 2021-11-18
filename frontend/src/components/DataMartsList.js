import React, {Component} from 'react';
import parseRequestParams from 'utils/parseRequestParams';


export default class DataMartsList extends Component {

  constructor(props) {
    super(props);
    this.state = {
      entry_points: props.entry_points,
      entry_point_id: props.entry_point_id,
    };
  }

  changeDataMart(mart_id) {
    const {entry_points} = this.props;

    let request_params = entry_points[mart_id].request_params || [];
    this.props.actions.changeActiveDataMart(mart_id);

    request_params = parseRequestParams(request_params);

    const {term_ids, subj_ids, limit, options_arr} = request_params;

    this.props.actions.notifyLoadingTerms();
    this.props.actions.loadTree(mart_id, term_ids);

    let request_options = {};

    request_options.terms = term_ids;
    request_options.offset = 0;
    if (limit > -1)
      request_options.limit = limit;

    this.props.actions.notifyLoadingEntities();
    const params = {
      options_obj: request_options,
      mart_id,
      subj_ids,
      options_arr
    };
    this.props.actions.getEntities(params);
  }

  render() {
    const {entry_points, entry_point_id} = this.props;

    let is_active = (pk) => pk === entry_point_id;
    const keys = Object.keys(entry_points);
    let dataMarts = [];

    // Используем 2 цикла для сортировки витрин данных, если был передан параметр order.
    // Если не был передан параметр, то одной итерацией добавляем витрины в массив dataMarts и выводим его в том порядке,
    // в котором получили.
    for (let i = 1; i <= keys.length; i++) {
      for (let j = 0; j < keys.length; j++) {
        if (entry_points[keys[j]].order && entry_points[keys[j]].order !== i)
          continue;

        const item = entry_points[keys[j]];

        let item_vis;
        if (is_active(keys[j]) && item.url)
          item_vis = <a href={item.url}>{item.name}</a>;
        else
          item_vis = item.name;

        dataMarts.push(
          <li key={`datamart-list_${j}`}
              className={is_active(keys[j]) ? 'active' : ''}
              onClick={() => is_active(keys[j]) ? null : this.changeDataMart(keys[j])}>
            <span>{item_vis}</span>
          </li>
        );

        if (entry_points[keys[0]].order)
          break;
      }

      if (!entry_points[keys[0]].order)
        break;
    }

    return entry_points && Object.keys(entry_points).length > 1 ? <div>
      <ul className="datamart-list">
        {dataMarts}
      </ul>
    </div> : null;
  }
}
