import {
  CHANGE_ACTIVE_DATA_MART,
} from '../constants/TermsTree';


const datamart_list = (state = {}, action) => {
  switch (action.type) {
    case CHANGE_ACTIVE_DATA_MART:
      return Object.assign({}, state, {
        active_mart_id: action.active_mart_id,
      });
    default:
      return state;
  }
};


export default datamart_list;

