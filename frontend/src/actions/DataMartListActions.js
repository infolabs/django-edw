import {
  SET_DATA_MART_LIST,
  CHANGE_ACTIVE_DATA_MART
} from '../constants/DataMartList'


export function set_data_mart_list(data_marts, mart_id) {
  return dispatch => {
    dispatch({
      type: SET_DATA_MART_LIST,
      data_marts,
      mart_id
    })
  }
}

export function change_active_data_mart(active) {
  return dispatch => {
    dispatch({
      type: CHANGE_ACTIVE_DATA_MART,
      active
    })
  }
}