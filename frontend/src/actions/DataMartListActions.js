import {
  CHANGE_ACTIVE_DATA_MART
} from '../constants/TermsTree.js'


export function changeActiveDataMart(active_mart_id) {
  return dispatch => {
    dispatch({
      type: CHANGE_ACTIVE_DATA_MART,
      active_mart_id
    })
  }
}
