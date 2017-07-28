import {
  SET_DATA_MART_LIST,
  CHANGE_ACTIVE_DATA_MART
} from '../constants/DataMartList'


const datamart_list = (state=[], action) => {
  switch (action.type) {
    case SET_DATA_MART_LIST:
      return Object.assign({}, state, {
        data_marts: action.data_marts,
        active_mart: action.mart_id
      });
    case CHANGE_ACTIVE_DATA_MART:
      return Object.assign({}, state, {
        active_mart: action.active
      });
    default:
      return state
  }
};

export default datamart_list